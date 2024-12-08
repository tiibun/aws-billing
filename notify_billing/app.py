import boto3
import requests
from datetime import datetime, timedelta, date


def get_secret(secret_name):
    client = boto3.client("ssm")
    try:
        response = client.get_parameter(Name=secret_name, WithDecryption=True)
    except Exception as e:
        print(f"Error retrieving parameter {secret_name}: {e}")
        raise e
    else:
        return response["Parameter"]["Value"]


# シークレットを取得
LINE_ACCESS_TOKEN = get_secret("LINE_ACCESS_TOKEN")
LINE_USER_ID = get_secret("LINE_USER_ID")


def lambda_handler(event, context) -> None:
    client = boto3.client("ce", region_name="us-east-1")

    # 合計とサービスごとの請求額を取得する
    total_billing = get_total_billing(client)
    service_billings = get_service_billings(client)

    # Line用のメッセージを作成して投げる
    (title, detail) = get_message(total_billing, service_billings)
    post_line(title, detail)


def get_total_billing(client) -> dict:
    (start_date, end_date) = get_total_cost_date_range()

    response = client.get_cost_and_usage(
        TimePeriod={
            "Start": start_date,
            "End": end_date,
        },
        Granularity="MONTHLY",
        Metrics=["AmortizedCost"],
    )
    return {
        "start": response["ResultsByTime"][0]["TimePeriod"]["Start"],
        "end": response["ResultsByTime"][0]["TimePeriod"]["End"],
        "billing": response["ResultsByTime"][0]["Total"]["AmortizedCost"]["Amount"],
    }


def get_service_billings(client) -> list:
    (start_date, end_date) = get_total_cost_date_range()

    response = client.get_cost_and_usage(
        TimePeriod={
            "Start": start_date,
            "End": end_date,
        },
        Granularity="MONTHLY",
        Metrics=["AmortizedCost"],
        GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
    )

    billings = []

    for item in response["ResultsByTime"][0]["Groups"]:
        billings.append(
            {
                "service_name": item["Keys"][0],
                "billing": item["Metrics"]["AmortizedCost"]["Amount"],
            }
        )
    return billings


def get_message(total_billing: dict, service_billings: list) -> tuple[str, str]:
    start = datetime.strptime(total_billing["start"], "%Y-%m-%d").strftime("%m/%d")

    end_today = datetime.strptime(total_billing["end"], "%Y-%m-%d")
    end_yesterday = (end_today - timedelta(days=1)).strftime("%m/%d")

    total = round(float(total_billing["billing"]), 2)

    title = f"{start}~{end_yesterday}の請求額は {total:.2f} USDです。"

    details = []
    for item in service_billings:
        service_name = item["service_name"]
        billing = round(float(item["billing"]), 2)

        if billing == 0.0:
            continue
        details.append(f" ・{service_name}: {billing:.2f} USD")

    return title, "\n".join(details)


def post_line(title: str, detail: str) -> None:
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer %s" % LINE_ACCESS_TOKEN,
    }
    data = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": title + "\n" + detail}],
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(e)
    else:
        print(response.status_code)
        print(response.text)


def get_total_cost_date_range() -> tuple[str, str]:
    start_date = get_begin_of_month()
    end_date = get_today()

    if start_date == end_date:
        end_of_month = datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=-1)
        begin_of_month = end_of_month.replace(day=1)
        return begin_of_month.date().isoformat(), end_date
    return start_date, end_date


def get_begin_of_month() -> str:
    return date.today().replace(day=1).isoformat()


def get_prev_day(prev: int) -> str:
    return (date.today() - timedelta(days=prev)).isoformat()


def get_today() -> str:
    return date.today().isoformat()
