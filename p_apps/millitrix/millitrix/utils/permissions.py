
def assert_user_rights(user):
    if not user:
        raise Exception("Unauthorized")
    return True
