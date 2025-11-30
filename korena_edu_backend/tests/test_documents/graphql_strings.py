"""GraphQL operation strings for documents-related tests."""

MY_DOCUMENTS_QUERY = """
query MyDocuments($level: String) {
  myDocuments(level: $level) {
    id
    title
    description
    type {
      id
      code
      level
    }
    currentVersion {
      id
      status
      source
    }
    isArchived
    createdAt
    updatedAt
  }
}
"""

DOCUMENT_QUERY = """
query Document($id: ID!) {
  document(id: $id) {
    id
    title
    description
    type {
      id
      code
      level
    }
    currentVersion {
      id
      status
      source
    }
    isArchived
    createdAt
    updatedAt
  }
}
"""

CREATE_DOCUMENT_MUTATION = """
mutation CreateDocument(
  $documentTypeCode: String!
  $title: String
  $description: String
  $schoolId: ID
) {
  createDocument(
    documentTypeCode: $documentTypeCode
    title: $title
    description: $description
    schoolId: $schoolId
  ) {
    document {
      id
      title
      description
      type {
        id
        code
        level
      }
      isArchived
      createdAt
      updatedAt
    }
  }
}
"""

__all__ = [
    "MY_DOCUMENTS_QUERY",
    "DOCUMENT_QUERY",
    "CREATE_DOCUMENT_MUTATION",
]
