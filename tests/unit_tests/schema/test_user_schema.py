from datetime import datetime
from uuid import uuid4

from app.schema.task_schema import TaskPointsResponseByUser
from app.schema.user_schema import (BaseUser, PostAssignPointsToUser,
                                    PostPointsConversionRequest,
                                    ResponseConversionPreview, ResponsePointsConversion,
                                    UserBasicInfo, UserPointsTasks, UserWallet)
from app.schema.wallet_schema import WalletWithoutUserId
from app.schema.wallet_transaction_schema import BaseWalletTransactionInfo


def test_base_user():
    """
    Test the BaseUser model.

    The BaseUser model is used as a base model for a user.

    The model has the following attributes:
    - externalUserId (str): External user ID
    """
    data = {"externalUserId": "user123"}
    user = BaseUser(**data)
    assert user.externalUserId == data["externalUserId"]


def test_user_basic_info():
    """
    Test the UserBasicInfo model.

    The UserBasicInfo model is used for basic user information.
    """
    data = {
        "id": uuid4(),
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "externalUserId": "user123",
    }
    user_info = UserBasicInfo(**data)
    assert user_info.id == data["id"]
    assert user_info.created_at == data["created_at"]
    assert user_info.updated_at == data["updated_at"]
    assert user_info.externalUserId == data["externalUserId"]


def test_post_assign_points_to_user():
    """
    Test the PostAssignPointsToUser model.

    The PostAssignPointsToUser model is used for assigning points to a user.
    """
    data = {
        "taskId": uuid4(),
        "points": 100,
        "description": "Good job",
        "data": {"extra": "value"},
    }
    assign_points = PostAssignPointsToUser(**data)
    assert assign_points.taskId == data["taskId"]
    assert assign_points.points == data["points"]
    assert assign_points.description == data["description"]
    assert assign_points.data == data["data"]


def test_user_wallet():
    """
    Test the UserWallet model.

    The UserWallet model is used for a user wallet.
    """
    wallet_data = {"coinsBalance": 100.0, "pointsBalance": 200.0, "conversionRate": 1.5}

    wallet_transaction_data = {
        "id": uuid4(),
        "created_at": str(datetime.now()),
        "transactionType": "reward",
        "points": 100,
        "coins": 50.0,
    }

    data = {
        "userId": "user123",
        "wallet": WalletWithoutUserId(**wallet_data),
        "walletTransactions": [BaseWalletTransactionInfo(**wallet_transaction_data)],
    }
    user_wallet = UserWallet(**data)
    assert user_wallet.userId == data["userId"]
    assert user_wallet.wallet.coinsBalance == wallet_data["coinsBalance"]
    assert user_wallet.wallet.pointsBalance == wallet_data["pointsBalance"]
    assert user_wallet.wallet.conversionRate == wallet_data["conversionRate"]
    assert user_wallet.walletTransactions[0].id == (wallet_transaction_data["id"])
    assert user_wallet.walletTransactions[0].transactionType == (
        wallet_transaction_data["transactionType"]
    )
    assert user_wallet.walletTransactions[0].points == (
        wallet_transaction_data["points"]
    )
    assert user_wallet.walletTransactions[0].coins == (wallet_transaction_data["coins"])


def test_user_points_tasks():
    """
    Test the UserPointsTasks model.

    The UserPointsTasks model is used for user points tasks.
    """
    task_points_data = {
        "taskId": "task123",
        "externalTaskId": "task123",
        "gameId": "game123",
        "points": 100,
    }
    data = {"id": uuid4(), "tasks": [TaskPointsResponseByUser(**task_points_data)]}
    user_points_tasks = UserPointsTasks(**data)
    assert user_points_tasks.id == data["id"]
    assert user_points_tasks.tasks[0].taskId == task_points_data["taskId"]
    assert user_points_tasks.tasks[0].externalTaskId == (
        task_points_data["externalTaskId"]
    )
    assert user_points_tasks.tasks[0].gameId == task_points_data["gameId"]
    assert user_points_tasks.tasks[0].points == task_points_data["points"]


def test_response_conversion_preview():
    """
    Test the ResponseConversionPreview model.

    The ResponseConversionPreview model is used for conversion preview
      response.
    """
    data = {
        "points": 100,
        "conversionRate": 1.5,
        "conversionRateDate": "2023-01-01",
        "convertedAmount": 150.0,
        "convertedCurrency": "USD",
        "haveEnoughPoints": True,
    }
    conversion_preview = ResponseConversionPreview(**data)
    assert conversion_preview.points == data["points"]
    assert conversion_preview.conversionRate == data["conversionRate"]
    assert conversion_preview.conversionRateDate == data["conversionRateDate"]
    assert conversion_preview.convertedAmount == data["convertedAmount"]
    assert conversion_preview.convertedCurrency == data["convertedCurrency"]
    assert conversion_preview.haveEnoughPoints == data["haveEnoughPoints"]


def test_post_points_conversion_request():
    """
    Test the PostPointsConversionRequest model.

    The PostPointsConversionRequest model is used for points conversion
      request.
    """
    data = {"points": 100}
    points_conversion_request = PostPointsConversionRequest(**data)
    assert points_conversion_request.points == data["points"]


def test_response_points_conversion():
    """
    Test the ResponsePointsConversion model.

    The ResponsePointsConversion model is used for points conversion response.
    """
    data = {
        "transactionId": "txn123",
        "points": 100,
        "conversionRate": 1.5,
        "conversionRateDate": "2023-01-01",
        "convertedAmount": 150.0,
        "convertedCurrency": "USD",
        "haveEnoughPoints": True,
    }
    points_conversion = ResponsePointsConversion(**data)
    assert points_conversion.transactionId == data["transactionId"]
    assert points_conversion.points == data["points"]
    assert points_conversion.conversionRate == data["conversionRate"]
    assert points_conversion.conversionRateDate == data["conversionRateDate"]
    assert points_conversion.convertedAmount == data["convertedAmount"]
    assert points_conversion.convertedCurrency == data["convertedCurrency"]
    assert points_conversion.haveEnoughPoints == data["haveEnoughPoints"]
