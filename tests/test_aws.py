from moto import mock_aws

from spendsentry.providers.aws import AWSProvider


@mock_aws
def test_aws_provider():
    provider = AWSProvider()
    assert provider is not None

    # We could do more thorough testing with mocked CE API
    # but that is a bit involved for Moto's current CE support.
    # At least testing we can instantiate it and it's imported correctly.
