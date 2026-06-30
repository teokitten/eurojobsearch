import app as eurojob_app


class _FakeResponse:
    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


def test_fetch_profession_hu_parses_card(monkeypatch):
    html = """
    <div class="dsx-card__content">
      <h2>
        <a href="https://www.profession.hu/allas/python-fejleszto-example-123">Python Fejleszto</a>
      </h2>
      <a title="Example karrier">
        <span class="details-text">Example Kft.</span>
      </a>
      <li id="details-location">
        <span class="details-text">Hibrid • Budapest</span>
      </li>
    </div>
    """

    monkeypatch.setattr(eurojob_app, "_source_request", lambda *args, **kwargs: _FakeResponse(html))

    jobs, warnings = eurojob_app._fetch_profession_hu("python")

    assert warnings == []
    assert len(jobs) == 1
    assert jobs[0]["source"] == "PROFESSION_HU"
    assert jobs[0]["company"] == "Example Kft."
    assert jobs[0]["location"] == "Hibrid • Budapest"
    assert jobs[0]["is_hybrid"] is True


def test_fetch_nofluffjobs_parses_card(monkeypatch):
    html = """
    <a class="posting-list-item" href="/hu/job/python-developer-example">
      <h3 data-cy="title position on the job offer listing">Python Developer</h3>
      <span data-cy="salary ranges on the job offer listing">1.2M - 1.6M HUF</span>
      <span data-cy="category name on the job offer listing">Backend</span>
      <span data-cy="category name on the job offer listing">Python</span>
      <h4 class="company-name">Example Hungary Kft.</h4>
      <div data-cy="location on the job offer listing">Távmunka</div>
    </a>
    """

    monkeypatch.setattr(eurojob_app, "_source_request", lambda *args, **kwargs: _FakeResponse(html))

    jobs, warnings = eurojob_app._fetch_nofluffjobs("python")

    assert warnings == []
    assert len(jobs) == 1
    assert jobs[0]["source"] == "NOFLUFFJOBS"
    assert jobs[0]["company"] == "Example Hungary Kft."
    assert jobs[0]["job_type"] == "1.2M - 1.6M HUF"
    assert jobs[0]["location"] == "Remote"
    assert jobs[0]["is_remote"] is True
    assert jobs[0]["url"] == "https://nofluffjobs.com/hu/job/python-developer-example"
