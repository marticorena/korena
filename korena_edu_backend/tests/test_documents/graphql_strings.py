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

UPLOAD_DOCUMENT_VERSION_MUTATION = """
mutation UploadDocumentVersion($documentId: ID!, $file: Upload!) {
  uploadDocumentVersion(documentId: $documentId, file: $file) {
    documentVersion {
      id
      status
      source
      createdAt
      createdBy {
        id
        email
      }
    }
    document {
      id
      title
      currentVersion {
        id
        status
      }
      type {
        id
        level
      }
    }
  }
}
"""
