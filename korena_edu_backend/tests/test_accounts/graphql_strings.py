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

VERIFY_EMAIL_MUTATION = """
mutation VerifyEmail($token: String!) {
  verifyEmail(token: $token) {
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

LOGIN_USER_MUTATION = """
mutation LoginUser($email: String!, $password: String!) {
  loginUser(email: $email, password: $password) {
    accessToken
    refreshToken
  }
}
"""
