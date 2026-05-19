import pytest

from server import (
    Dataset,
    format_speaker_info,
    format_talk_detail,
    format_talks_table,
)


class TestDataset:
    def test_indexes_built(self, sample_dataset: Dataset):
        assert len(sample_dataset.talks) == 4
        assert sample_dataset.day_to_date("1") == "2026-05-19"
        assert sample_dataset.day_to_date("2") == "2026-05-20"
        assert sample_dataset.day_to_date("2026-05-19") == "2026-05-19"
        assert sample_dataset.day_to_date("2099-01-01") is None

    def test_talks_for_day(self, sample_dataset):
        d1 = sample_dataset.talks_for_day("2026-05-19")
        assert {t["agenda_id"] for t in d1} == {"7479", "7615"}
        d2 = sample_dataset.talks_for_day("2026-05-20")
        assert {t["agenda_id"] for t in d2} == {"7122", "7200"}

    def test_talks_for_room_substring(self, sample_dataset):
        out = sample_dataset.talks_for_room("cloudlounge")
        assert [t["agenda_id"] for t in out] == ["7122"]

    def test_talks_for_focus_excludes_no_mainfocus(self, sample_dataset):
        out = sample_dataset.talks_for_focus("devops")
        assert [t["agenda_id"] for t in out] == ["7122"]
        # 'No mainfocus' must not be considered a real focus
        assert sample_dataset.talks_for_focus("no main") == []

    def test_all_focuses(self, sample_dataset):
        assert set(sample_dataset.all_focuses) == {"DevOps", "AI & ML"}


class TestFormatters:
    def test_format_talks_table(self, sample_dataset):
        out = format_talks_table(sample_dataset.talks_for_day("2026-05-20"))
        assert "| ID | Date" in out
        assert "Java, Spring Boot" in out
        assert "AI Agents in Production" in out
        assert "DevOps" in out
        assert "AI & ML" in out

    def test_format_talks_table_empty(self):
        assert format_talks_table([]) == "No sessions found."

    def test_format_talk_detail_includes_abstract_and_speakers(self, sample_dataset):
        out = format_talk_detail(sample_dataset.talk("7122"))
        assert "# Java, Spring Boot, GitOps & Kubernetes" in out
        assert "## Abstract" in out
        assert "GitOps ist ein Ansatz" in out
        assert "Thomas Michael" in out
        assert "Cloudogu GmbH" in out
        assert "speaker_id: 13989" in out
        assert "Java, SpringBoot, Kubernetes, GitOps" in out

    def test_format_talk_detail_no_detail_block(self, sample_dataset):
        out = format_talk_detail(sample_dataset.talk("7479"))
        assert "# Doors Open & Warm-Up" in out
        assert "## Abstract" not in out

    def test_format_speaker_info_surfaces_pii(self, sample_dataset):
        s = sample_dataset.speakers["13989"]
        out = format_speaker_info(s)
        assert "# Thomas Michael" in out
        assert "Cloudogu GmbH" in out
        assert "https://www.linkedin.com/in/thomas-michael-30b941186/" in out
        assert "http://blog.thomasmichael.de" in out
        assert "## Bio" in out
        assert "Java, Spring Boot, GitOps & Kubernetes" in out


class TestTools:
    @pytest.mark.asyncio
    async def test_get_schedule_overview(self):
        from server import get_schedule_overview
        out = await get_schedule_overview()
        assert "CloudLand 2026" in out
        assert "2026-05-19" in out
        assert "2026-05-20" in out
        assert "DevOps" in out
        assert "AI & ML" in out
        assert "CloudLounge 1 Datev" in out

    @pytest.mark.asyncio
    async def test_get_talks_by_day_iso(self):
        from server import get_talks_by_day
        out = await get_talks_by_day("2026-05-20")
        assert "Java, Spring Boot" in out
        assert "AI Agents in Production" in out

    @pytest.mark.asyncio
    async def test_get_talks_by_day_index(self):
        from server import get_talks_by_day
        out = await get_talks_by_day("1")
        assert "Doors Open" in out
        assert "Karaoke Night" in out

    @pytest.mark.asyncio
    async def test_get_talks_by_day_not_found(self):
        from server import get_talks_by_day
        out = await get_talks_by_day("2099-01-01")
        assert "No sessions found" in out

    @pytest.mark.asyncio
    async def test_get_talks_by_room(self):
        from server import get_talks_by_room
        out = await get_talks_by_room("hispaniola")
        assert "AI Agents in Production" in out

    @pytest.mark.asyncio
    async def test_get_talks_by_focus(self):
        from server import get_talks_by_focus
        out = await get_talks_by_focus("AI")
        assert "AI Agents in Production" in out
        assert "Java, Spring Boot" not in out

    @pytest.mark.asyncio
    async def test_get_talk_details(self):
        from server import get_talk_details
        out = await get_talk_details("7122")
        assert "# Java, Spring Boot, GitOps & Kubernetes" in out
        assert "GitOps ist ein Ansatz" in out
        assert "Thomas Michael" in out

    @pytest.mark.asyncio
    async def test_get_talk_details_not_found(self):
        from server import get_talk_details
        out = await get_talk_details("9999")
        assert "No session" in out

    @pytest.mark.asyncio
    async def test_search_talks_by_keyword(self):
        from server import search_talks
        out = await search_talks("kubernetes")
        assert "Java, Spring Boot" in out
        # Abstract preview included for agent chaining
        assert "**Abstract:**" in out

    @pytest.mark.asyncio
    async def test_search_talks_by_speaker(self):
        from server import search_talks
        out = await search_talks("anna")
        assert "AI Agents in Production" in out

    @pytest.mark.asyncio
    async def test_search_talks_no_results(self):
        from server import search_talks
        out = await search_talks("quantum-blockchain-fusion")
        assert "No sessions found" in out

    @pytest.mark.asyncio
    async def test_get_speaker_info_substring(self):
        from server import get_speaker_info
        out = await get_speaker_info("thomas")
        assert "# Thomas Michael" in out
        assert "Cloudogu GmbH" in out
        # PII for the censoring demo
        assert "linkedin.com" in out

    @pytest.mark.asyncio
    async def test_get_speaker_info_not_found(self):
        from server import get_speaker_info
        out = await get_speaker_info("nobody")
        assert "No speaker matching" in out
