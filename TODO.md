1. **Request Validator** 
 - Validate incoming requests against OpenAPI schema
 - Path Parameters - Extract path params (like {art_object_id}) into request data
 - Query Parameters - Handle query string params per OpenAPI spec
 - Type coercion and format validation: Implementation receives a dictionary or array of dictionaries with typed values?  - how do we get typed data?

2. **Error Middleware** using 
   - Standard error response format
   - Map business exceptions to HTTP status codes
   - Validation error formatting

3. **Response Validation**
   - Validate outgoing responses against schema
   - Optional in production, strict in development

### Phase 3: Authentication & Configuration
1. **Auth Middleware** 
   - API key authentication  
   - Pass auth context to implementation

2. **Configuration System**
   - Environment-specific settings - does it need this - handled outside of this?

