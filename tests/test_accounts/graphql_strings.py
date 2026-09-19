"""Reusable GraphQL operation strings for accounts-related tests.

These queries and mutations are aligned with the current Strawberry schema.
"""

ME_QUERY = """
query Me {
  me {
    id
    email
    firstName
    lastName
    role
  }
}
"""

LOGIN_USER_MUTATION = """
mutation LoginUser($email: String!, $password: String!) {
  loginUser(email: $email, password: $password) {
    access
    refresh
  }
}
"""

REFRESH_TOKEN_MUTATION = """
mutation RefreshToken($refresh: String!) {
  refreshToken(refresh: $refresh) {
    access
    refresh
  }
}
"""

VERIFY_TOKEN_MUTATION = """
mutation VerifyToken($token: String!) {
  verifyToken(token: $token)
}
"""

REGISTER_USER_MUTATION = """
mutation RegisterUser(
  $email: String!,
  $password1: String!,
  $password2: String!,
  $firstName: String!,
  $lastName: String!
) {
  registerUser(
    email: $email,
    password1: $password1,
    password2: $password2,
    firstName: $firstName,
    lastName: $lastName
  ) {
    token
  }
}
"""

ACTIVATE_ACCOUNT_MUTATION = """
mutation ActivateAccount($token: String!) {
  activateAccount(token: $token) {
    email
  }
}
"""

UPDATE_USER_MUTATION = """
mutation UpdateUser($firstName: String!, $lastName: String!) {
  updateUser(firstName: $firstName, lastName: $lastName) {
    email
  }
}
"""

CHANGE_PASSWORD_MUTATION = """
mutation ChangePassword(
  $currentPassword: String!,
  $password1: String!,
  $password2: String!
) {
  changePassword(
    currentPassword: $currentPassword,
    password1: $password1,
    password2: $password2
  ) {
    email
  }
}
"""

DELETE_ACCOUNT_MUTATION = """
mutation DeleteAccount($currentPassword: String!) {
  deleteAccount(currentPassword: $currentPassword) {
    email
  }
}
"""

__all__ = [
    "ME_QUERY",
    "LOGIN_USER_MUTATION",
    "REFRESH_TOKEN_MUTATION",
    "VERIFY_TOKEN_MUTATION",
    "REGISTER_USER_MUTATION",
    "ACTIVATE_ACCOUNT_MUTATION",
    "UPDATE_USER_MUTATION",
    "CHANGE_PASSWORD_MUTATION",
    "DELETE_ACCOUNT_MUTATION",
]
