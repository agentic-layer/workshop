import pytest


SAMPLE = {
    "conference": {
        "name": "CloudLand 2026",
        "venue": "Heide Park Soltau, Germany",
        "host": "DOAG",
        "url": "https://my.doag.org/events/cloudland/2026/agenda/",
        "start_date": "2026-05-19",
        "end_date": "2026-05-20",
        "timezone": "Europe/Berlin",
        "scraped_at": "2026-05-19T11:48:58+00:00",
        "scraper_user_agent": "felix.kampfer@qaware.de",
    },
    "days": ["2026-05-19", "2026-05-20"],
    "rooms": ["Captain Hook", "CloudLounge 1 Datev", "Hispaniola"],
    "talks": [
        {
            "agenda_id": "7122",
            "event_slot_id": "20022",
            "date": "2026-05-20",
            "date_agenda_ts": 1779228000,
            "start_time": "12:00",
            "end_time": "12:45",
            "title": "Java, Spring Boot, GitOps & Kubernetes",
            "speaker_string": "Thomas Michael",
            "room": "CloudLounge 1 Datev",
            "language_code": "de",
            "detail": {
                "title": "Java, Spring Boot, GitOps & Kubernetes",
                "room_capacity": 20,
                "speakers": [
                    {
                        "contributor_id": "13989",
                        "name": "Thomas Michael",
                        "company": "Cloudogu GmbH",
                        "photo_url": "https://my.doag.org/x.jpg",
                    }
                ],
                "key_data": {
                    "Language": "German",
                    "Main Focus": "DevOps",
                    "Lecture Type": "Interactive Experiences",
                },
                "abstract": "GitOps ist ein Ansatz für reproduzierbare Deployments.\n\nKubernetes, Helm, Kustomize.",
                "keywords": ["Java", "SpringBoot", "Kubernetes", "GitOps"],
            },
        },
        {
            "agenda_id": "7479",
            "event_slot_id": None,
            "date": "2026-05-19",
            "date_agenda_ts": 1779141600,
            "start_time": "09:30",
            "end_time": "10:30",
            "title": "Doors Open & Warm-Up",
            "speaker_string": "",
            "room": "Captain Hook",
            "language_code": None,
            "detail": None,
        },
        {
            "agenda_id": "7615",
            "event_slot_id": "20415",
            "date": "2026-05-19",
            "date_agenda_ts": 1779141600,
            "start_time": "21:00",
            "end_time": "02:00",
            "title": "Karaoke Night",
            "speaker_string": "",
            "room": "Captain Hook",
            "language_code": None,
            "detail": {
                "title": "Karaoke Night",
                "room_capacity": 300,
                "speakers": [],
                "key_data": {"Main Focus": "No mainfocus", "Lecture Type": "Community"},
                "abstract": "Grab the mic and sing.",
                "keywords": [],
            },
        },
        {
            "agenda_id": "7200",
            "event_slot_id": "20100",
            "date": "2026-05-20",
            "date_agenda_ts": 1779228000,
            "start_time": "14:00",
            "end_time": "14:45",
            "title": "AI Agents in Production",
            "speaker_string": "Anna Schmidt",
            "room": "Hispaniola",
            "language_code": "en",
            "detail": {
                "title": "AI Agents in Production",
                "room_capacity": 80,
                "speakers": [
                    {
                        "contributor_id": "14001",
                        "name": "Anna Schmidt",
                        "company": "QAware GmbH",
                        "photo_url": None,
                    }
                ],
                "key_data": {
                    "Language": "English",
                    "Main Focus": "AI & ML",
                    "Lecture Type": "Deep-dive",
                },
                "abstract": "Building reliable LLM-driven agents with Claude.",
                "keywords": ["AI", "Agents", "LLM"],
            },
        },
    ],
    "speakers": {
        "13989": {
            "contributor_id": "13989",
            "name": "Thomas Michael",
            "company": "Cloudogu GmbH",
            "board_position": "CloudLand 2026 Speaker",
            "photo_url": "https://my.doag.org/x.jpg",
            "bio": "DevOps consultant working with GitOps tooling.",
            "labelled_links": {
                "website": "http://blog.thomasmichael.de",
                "blog": "http://blog.thomasmichael.de",
            },
            "socials": {"linkedin": "https://www.linkedin.com/in/thomas-michael-30b941186/"},
            "talk_ids": ["7122"],
        },
        "14001": {
            "contributor_id": "14001",
            "name": "Anna Schmidt",
            "company": "QAware GmbH",
            "board_position": "CloudLand 2026 Speaker",
            "photo_url": None,
            "bio": "",
            "labelled_links": {},
            "socials": {"twitter": "https://twitter.com/anna"},
            "talk_ids": ["7200"],
        },
    },
}


@pytest.fixture
def sample_dataset():
    from server import Dataset
    return Dataset(SAMPLE)


@pytest.fixture(autouse=True)
def _patch_module_dataset(monkeypatch, sample_dataset):
    import server
    monkeypatch.setattr(server, "dataset", sample_dataset)
