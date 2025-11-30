"""GraphQL operation strings for documents-related tests."""

MY_DOCUMENTS_QUERY = """
query MyDocuments($level: String) {
  myDocuments(level: $level) {
    id
    title
    description
    category {
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
    category {
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
  $documentCategoryCode: String!
  $title: String
  $description: String
  $schoolId: ID
) {
  createDocument(
    documentCategoryCode: $documentCategoryCode
    title: $title
    description: $description
    schoolId: $schoolId
  ) {
    document {
      id
      title
      description
      category {
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

CREATE_DOCUMENT_CATEGORY_MUTATION = """
mutation CreateDocumentCategory(
  $code: String!
  $name: String!
  $level: String!
  $description: String
  $isOfficial: Boolean
  $mineduReference: String
) {
  createDocumentCategory(
    code: $code
    name: $name
    level: $level
    description: $description
    isOfficial: $isOfficial
    mineduReference: $mineduReference
  ) {
    documentCategory {
      id
      code
      name
      description
      level
      isOfficial
      mineduReference
    }
  }
}
"""

__all__ = [
    "MY_DOCUMENTS_QUERY",
    "DOCUMENT_QUERY",
    "CREATE_DOCUMENT_MUTATION",
    "CREATE_DOCUMENT_CATEGORY_MUTATION",
]
