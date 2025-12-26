# Registration Feature Architecture Design

## Architectural Overview

Following the architect agent's analysis of existing codebase patterns, this design ensures seamless integration with the current JWT-based authentication system while maintaining consistency with established patterns.

## Design Principles Applied

### 1. **Testability** 
- Clear separation of concerns between UI, validation, and service layers
- Injectable dependencies through existing hook patterns
- Isolated form state management for unit testing

### 2. **Readability**
- Consistent naming conventions with existing auth system
- Clear interfaces matching LoginPage patterns  
- Self-documenting component structure

### 3. **Consistency**
- Mirrors existing LoginPage architecture
- Uses established validation patterns
- Follows current error handling approach

### 4. **Simplicity** 
- Extends existing services rather than creating parallel systems
- Reuses existing form validation patterns
- Minimal new abstractions

### 5. **Reversibility**
- Non-breaking changes to existing auth system
- Feature can be disabled/removed without affecting login
- Maintains existing API contracts

## Existing Pattern Analysis

### Component Architecture (from LoginPage.tsx)
```
LoginPage Component:
├── Form State Management (useState<LoginFormState>)
├── Authentication Integration (useAuth hook)
├── Validation Logic (validateUsername, validatePassword)
├── Form Submission (handleSubmit)
├── UI Rendering (form fields, buttons, feedback)
└── Navigation Logic (redirect after success)
```

### Authentication Service Pattern (from authService.ts)
```
AuthService:
├── login(credentials) → LoginResponse
├── validateToken(token) → boolean  
├── refreshToken(token) → LoginResponse
└── logout(token) → void
```

**Offline Access:** When the MCP transport is unavailable, `authService.login`
falls back to a local, hashed credential store that mirrors the demo admin/user
accounts. The fallback keeps JWT issuance and session creation identical to the
online path, only bypassing the remote `login` tool. Connection errors are
tracked so that the client avoids spamming toast notifications while continuing
to surface a single failure alert to the user.

**Token Resilience:** If the Web Crypto powered JWT generator is unavailable,
the service emits deterministic, base64-prefixed `offline-access-*` and
`offline-refresh-*` tokens so demos remain functional while clearly signalling
they were produced through the offline path.

### Type Definition Pattern (from auth.ts)
```
Authentication Types:
├── User interface (id, username, email, role)
├── LoginCredentials interface
├── LoginFormState interface  
├── LoginResponse interface
└── Validation interfaces
```

## Registration Architecture Design

### 1. Type Definitions Extension

**File:** `/src/types/auth.ts`

```typescript
// Registration credentials interface
export interface RegistrationCredentials {
  username: string
  email: string
  password: string
  confirmPassword: string
  role?: 'admin' | 'user'  // Default: 'user'
  acceptTerms: boolean
}

// Registration form state (mirrors LoginFormState pattern)
export interface RegistrationFormState {
  username: {
    value: string
    error?: string
    isValid: boolean
  }
  email: {
    value: string
    error?: string
    isValid: boolean
  }
  password: {
    value: string
    error?: string
    isValid: boolean
    strength?: PasswordStrength
  }
  confirmPassword: {
    value: string
    error?: string
    isValid: boolean
  }
  acceptTerms: {
    value: boolean
    error?: string
    isValid: boolean
  }
  isSubmitting: boolean
  submitError: string
}

// Password strength for registration (not login)
export interface PasswordStrength {
  score: number // 0-4
  feedback: string[]
  requirements: {
    minLength: boolean
    hasUppercase: boolean
    hasLowercase: boolean
    hasNumber: boolean
    hasSpecialChar: boolean
  }
}

// Registration response
export interface RegistrationResponse extends LoginResponse {
  isEmailVerified: boolean
  verificationToken?: string
}
```

### 2. Service Layer Extension

**File:** `/src/services/auth/authService.ts` (extend existing)

```typescript
class AuthService {
  // ... existing methods

  /**
   * Register new user with credentials
   */
  async register(credentials: RegistrationCredentials): Promise<RegistrationResponse> {
    await this.ensureInitialized()
    
    // Validate registration data
    await this.validateRegistrationCredentials(credentials)
    
    // Create user account (mock implementation)
    const user = await this.createUserAccount(credentials)
    
    // Generate JWT tokens for new user
    const jwtOptions: JWTGenerationOptions = {
      userId: user.id,
      username: user.username,
      email: user.email,
      role: user.role,
      sessionId: this.generateSessionId(),
      userAgent: navigator.userAgent,
      ipAddress: await this.getClientIP(),
      tokenType: 'access',
      scope: user.role === 'admin' ? ['read', 'write', 'admin'] : ['read']
    }
    
    // Generate tokens
    const [accessToken, refreshToken] = await Promise.all([
      jwtService.generateToken({ ...jwtOptions, tokenType: 'access' }),
      jwtService.generateToken({ ...jwtOptions, tokenType: 'refresh' })
    ])
    
    return {
      user,
      token: accessToken,
      refreshToken,
      expiresIn: 3600,
      isEmailVerified: false,
      tokenType: 'JWT'
    }
  }

  private async validateRegistrationCredentials(
    credentials: RegistrationCredentials
  ): Promise<void> {
    // Username uniqueness check
    if (await this.usernameExists(credentials.username)) {
      throw new Error('Invalid username or password') // Generic error
    }
    
    // Email uniqueness check  
    if (await this.emailExists(credentials.email)) {
      throw new Error('Invalid username or password') // Generic error
    }
  }
}
```

### 3. Component Architecture

**File:** `/src/pages/RegistrationPage.tsx`

Following the exact pattern of LoginPage.tsx:

```typescript
export function RegistrationPage() {
  const { login, isAuthenticated, isLoading, error } = useAuth()
  const location = useLocation()
  
  // Redirect after registration (same pattern as LoginPage)
  const from = (location.state as any)?.from?.pathname || '/'

  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [formState, setFormState] = useState<RegistrationFormState>({
    // Initial state structure
  })

  // Validation functions (similar to LoginPage pattern)
  const validateUsername = (value: string): ValidationResult => { /* */ }
  const validateEmail = (value: string): ValidationResult => { /* */ }
  const validatePassword = (value: string): ValidationResult => { /* */ }
  const validateConfirmPassword = (value: string): ValidationResult => { /* */ }

  // Form submission (mirrors LoginPage handleSubmit)
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    // Validation and submission logic
  }

  // UI rendering following LoginPage structure
  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20 flex items-center justify-center p-4">
      {/* Form structure mirrors LoginPage */}
    </div>
  )
}
```

### 4. Hook Integration

**File:** `/src/providers/AuthProvider.tsx` (extend existing)

```typescript
interface AuthContextType {
  // ... existing properties
  register: (credentials: RegistrationCredentials) => Promise<void>
}

export function AuthProvider({ children }: AuthProviderProps) {
  // ... existing code

  const register = useCallback(async (credentials: RegistrationCredentials) => {
    updateAuthState({ isLoading: true, error: null })

    try {
      const registrationResponse = await authService.register(credentials)
      
      // Create session (same as login flow)
      const sessionMetadata = await sessionService.createSession({
        userId: registrationResponse.user.id,
        rememberMe: false,
        userAgent: navigator.userAgent,
        ipAddress: 'localhost'
      })

      updateAuthState({
        user: registrationResponse.user,
        isAuthenticated: true,
        isLoading: false,
        error: null,
        sessionExpiry: sessionMetadata.expiryTime
      })
    } catch (error) {
      updateAuthState({
        isLoading: false,
        error: 'Invalid username or password' // Generic error
      })
      throw error
    }
  }, [updateAuthState])

  return (
    <AuthContext.Provider value={{ 
      ...existingValue, 
      register 
    }}>
      {children}
    </AuthContext.Provider>
  )
}
```

### 5. Routing Integration

**File:** `/src/App.tsx` (extend existing routes)

```typescript
// Add registration route following existing pattern
<Route path="/register" element={
  <PublicRoute>
    <RegistrationPage />
  </PublicRoute>
} />
```

## Architecture Decisions & Rationale

### Decision 1: Extend Existing Services vs. New Service
**Choice:** Extend existing authService
**Rationale:** 
- Maintains consistency with established patterns
- Reduces complexity and learning curve
- Leverages existing JWT integration
- Follows DRY principle

### Decision 2: Form State Management
**Choice:** Mirror LoginFormState pattern exactly
**Rationale:**
- Proven pattern already in use
- Consistent developer experience
- Testable and maintainable
- Follows project conventions

### Decision 3: Password Strength in Registration Only
**Choice:** Include password strength validation in registration, not login
**Rationale:**
- Registration is for creating new passwords (strength matters)
- Login is for existing passwords (strength not relevant)
- Follows UX best practices
- Maintains clean separation of concerns

### Decision 4: Generic Error Messages
**Choice:** Use same "Invalid username or password" pattern
**Rationale:**
- Consistent with existing security approach
- Prevents information disclosure
- Follows established security patterns
- Maintains security posture

### Decision 5: Auto-Login After Registration
**Choice:** Automatically log in user after successful registration
**Rationale:**
- Follows modern UX patterns
- Reduces friction in user journey
- Leverages existing session management
- Consistent with most applications

## Integration Points

### With Existing Authentication Flow
- Uses same JWT token generation system
- Integrates with existing session management  
- Follows same error handling patterns
- Maintains existing security measures

### With UI/UX Patterns
- Mirrors LoginPage component structure
- Uses existing form validation patterns
- Follows established loading states
- Maintains consistent visual design

### With Testing Infrastructure
- Testable through same patterns as LoginPage
- Uses established mocking strategies
- Integrates with existing test utilities
- Follows current testing conventions

## Risk Mitigation

### Security Risks
- **Mitigation:** Mandatory security-auditor agent review
- **Validation:** OWASP Top 10 assessment required
- **Testing:** Security-specific test scenarios

### Integration Risks  
- **Mitigation:** Follow established patterns exactly
- **Validation:** Comprehensive integration testing
- **Rollback:** Non-breaking changes allow easy rollback

### Performance Risks
- **Mitigation:** Leverage existing JWT infrastructure
- **Validation:** Performance testing in Stage 5
- **Monitoring:** Use existing performance monitoring

## Success Metrics

### Technical Metrics
- Zero breaking changes to existing authentication
- All TypeScript compilation passes
- 100-line limit compliance maintained
- Test coverage matches LoginPage standards

### User Experience Metrics  
- Registration flow completion rate
- User confusion/error rate
- Navigation flow efficiency
- Accessibility compliance

---
**Architecture Review Status:** Complete  
**Integration Risk:** Low (follows established patterns)  
**Security Risk:** Medium (requires security-auditor review)
**Implementation Complexity:** Low-Medium
