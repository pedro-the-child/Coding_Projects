"""
dlt source for Oura Ring v2 API.
Pulls a rolling lookback window (default 21 days) on every run — self-healing
against missed runs without relying on Airflow catchup.
"""
import dlt
from dlt.sources.helpers.rest_client import RESTClient
from dlt.sources.helpers.rest_client.paginators import SinglePagePaginator

from oauth_token_store import get_valid_access_token

import os
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv()

OURA_BASE_URL = "https://api.ouraring.com/v2/usercollection"
LOOKBACK_DAYS = int(os.environ.get("OURA_LOOKBACK_DAYS", 21))


def _client() -> RESTClient:
    token = get_valid_access_token()
    return RESTClient(
        base_url=OURA_BASE_URL,
        headers={"Authorization": f"Bearer {token}"},
        paginator=SinglePagePaginator(),
    )


def _date_range() -> tuple[str, str]:
    end = date.today()
    start = end - timedelta(days=LOOKBACK_DAYS)
    return start.isoformat(), end.isoformat()


@dlt.source(name="oura")
def oura_source():
    start_date, end_date = _date_range()
    client = _client()

    @dlt.resource(
        name="daily_sleep",
        write_disposition="merge",
        primary_key="id",
    )
    def daily_sleep():
        for page in client.paginate(
            "daily_sleep",
            params={"start_date": start_date, "end_date": end_date},
            data_selector="data",
        ):
            yield page

    @dlt.resource(
        name="sleep",
        write_disposition="merge",
        primary_key="id",
    )
    def sleep():
        for page in client.paginate(
            "sleep",
            params={"start_date": start_date, "end_date": end_date},
            data_selector="data",
        ):
            yield page

    @dlt.resource(
        name="daily_readiness",
        write_disposition="merge",
        primary_key="id",
    )
    def daily_readiness():
        for page in client.paginate(
            "daily_readiness",
            params={"start_date": start_date, "end_date": end_date},
            data_selector="data",
        ):
            yield page

    @dlt.resource(
        name="daily_activity",
        write_disposition="merge",
        primary_key="id",
    )
    def daily_activity():
        for page in client.paginate(
            "daily_activity",
            params={"start_date": start_date, "end_date": end_date},
            data_selector="data",
        ):
            yield page

    @dlt.resource(
        name="workout",
        write_disposition="merge",
        primary_key="id",
    )
    def workout():
        for page in client.paginate(
            "workout",
            params={"start_date": start_date, "end_date": end_date},
            data_selector="data",
        ):
            yield page

    @dlt.resource(
        name="heartrate",
        write_disposition="merge",
        primary_key=["timestamp"],
    )
    def heartrate():
        for page in client.paginate(
            "heartrate",
            params={"start_datetime": f"{start_date}T00:00:00", "end_datetime": f"{end_date}T23:59:59"},
            data_selector="data",
        ):
            yield page

    return daily_sleep, sleep, daily_readiness, daily_activity, workout, heartrate


if __name__ == "__main__":
    destination = os.environ.get("DLT_DESTINATION", "bigquery")
    pipeline = dlt.pipeline(
        pipeline_name="oura",
        destination=destination,
        dataset_name=os.environ.get("OURA_RAW_DATASET", "oura_raw"),
    )
    load_info = pipeline.run(oura_source())
    print(load_info)
