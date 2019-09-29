import os
import json
import uuid

from flask import Flask, Response, request
from http import HTTPStatus


def process_new_transaction():
    """Stores the incoming transaction body for processing and returns the identifier to check on processing progress

    Returns:
        str -- Unique identifier for retrieving the status of the transaction submitted
    """
    transaction_id = uuid.uuid4()

    # todo - store the body of the transaction in the bucket/file system

    return str(transaction_id)


def fetch_transaction_status(transaction_id):
    base = f"{request.host_url}v1"

    # todo - fetch the current status from the database

    status = {
        "complete": False,
        "status_url": f"{base}/transaction/{transaction_id}",
        "distribution": [
            {
                "partner": "trading_partner_1",
                "method": "sftp",
                "status": "pending",
                "location": "/var/edi/dropoff/transaction/my_file.edi",
                "confirmation": None,
            },
            {
                "partner": "source-archive",
                "method": "cloud-storage",
                "status": "complete",
                "location": f"s3://bucket-name/archive/{transaction_id}.edi",
                "confirmation": False,
            },
            {
                "partner": "result-archive",
                "method": "cloud-storage",
                "status": "pending",
                "location": f"s3://bucket-name/archive/{transaction_id}.edi",
                "confirmation": False,
            },
        ],
    }

    return status


def create_api_app(test_config=None):
    # Create and configure app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(SECRET_KEY=os.getenv("SECRET"))

    @app.route("/")
    def yield_api_versions():
        response = Response(
            response=json.dumps({"v1": f"{request.host_url}v1"}),
            status=int(HTTPStatus.OK),
            content_type="application/json",
        )
        return response

    @app.route("/v1")
    def yield_v1_endpoints():
        base = f"{request.host_url}v1"

        endpoints = {"transaction": f"{base}/transaction", "docs": f"{base}/docs"}

        response = Response(
            response=json.dumps(endpoints),
            status=int(HTTPStatus.OK),
            content_type="application/json",
        )

        return response

    @app.route("/v1/docs")
    def describe_v1_usage():
        base = f"{request.host_url}v1"
        doc_data = {
            f"{base}/transaction": {
                "GET": "Fetch a paginated list of transactions processed by the system",
                "POST": "Create a new transaction based on the body passed in. Supported transaction types include application/x12, application/json, application/edifact",
                "PUT": "Not supported on this endpoint",
                "PATCH": "Not supported on this endpoint",
                "DELETE": "Not supported on this endpoint",
            },
            base + "/transaction/{transaction_id}": {
                "GET": "Fetch details of the specified transaction",
                "POST": "Not supported on this endpoint",
                "PUT": "Not implemented",
                "PATCH": "Not implemented",
                "DELETE": "Not implemented",
            }
        }

        response = Response(
            response=json.dumps(doc_data),
            status=int(HTTPStatus.OK),
            content_type="application/json",
        )

        return response

    @app.route("/v1/transaction", methods=["GET"])
    def fetch_transaction_list():
        return Response(
            response=json.dumps({}),
            status=int(HTTPStatus.OK),
            content_type="application/json",
        )

    @app.route("/v1/transaction", methods=["POST"])
    def create_transaction_from_api_call():
        base = f"{request.host_url}v1"
        transaction_id = process_new_transaction()

        response = Response(
            response=json.dumps(fetch_transaction_status(transaction_id)),
            status=int(HTTPStatus.ACCEPTED),
            content_type="application/json",
        )

        response.headers["Location"] = f"{base}/transaction/{transaction_id}"

        return response

    @app.route("/v1/transaction", methods=["PUT", "PATCH", "DELETE"])
    @app.route("/v1/transaction/<transaction_id>", methods=["POST", "PUT", "PATCH", "DELETE"])
    def not_implemented():
        return Response(
            response=json.dumps({"error": "Method not supported on this endpoint"}),
            status=int(HTTPStatus.METHOD_NOT_ALLOWED),
            content_type="application/json",
        )

    @app.route("/v1/transaction/<transaction_id>", methods=["GET"])
    def fetch_transaction_by_id(transaction_id):
        transaction_data = fetch_transaction_status(transaction_id)

        return Response(
            response=json.dumps(transaction_data),
            status=int(HTTPStatus.OK),
            content_type="application/json"
        )

    return app


app = create_api_app()
