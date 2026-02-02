/**
 * ProfilePage Test Suite
 *
 * Tests for ProfilePage component including rendering,
 * profile display, password change, and i18n translations.
 *
 * Note: These tests mock useMCP with isConnected=false and rely on
 * the authUser fallback path to avoid async profile loading.
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { ProfilePage } from "./ProfilePage";

// Mock localStorage - must be before any imports that use it
const localStorageMock = {
  getItem: vi.fn(() => "mock-token"),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
Object.defineProperty(window, "localStorage", { value: localStorageMock });

// Mock sessionStorage
const sessionStorageMock = {
  getItem: vi.fn(() => null),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
Object.defineProperty(window, "sessionStorage", { value: sessionStorageMock });

// Setup hoisted mocks
const { mockUser, mockAddToast, mockCallTool } = vi.hoisted(() => {
  const mockUser = {
    id: "1",
    username: "testuser",
    email: "test@example.com",
    role: "admin" as const,
    isActive: true,
    lastLogin: "2024-01-01T12:00:00Z",
    createdAt: "2024-01-01T00:00:00Z",
  };

  const mockCallTool = vi.fn();
  const mockAddToast = vi.fn();

  return { mockUser, mockAddToast, mockCallTool };
});

// Mock providers
vi.mock("@/providers/AuthProvider", () => ({
  useAuth: () => ({
    user: mockUser,
    isAuthenticated: true,
    isLoading: false,
  }),
}));

// Mock MCP with isConnected=false - this causes the component to skip
// async profile loading and use the authUser fallback immediately
vi.mock("@/providers/MCPProvider", () => ({
  useMCP: () => ({
    client: { callTool: mockCallTool },
    isConnected: false,
    error: null,
  }),
}));

vi.mock("@/components/ui/Toast", () => ({
  useToast: () => ({
    addToast: mockAddToast,
    removeToast: vi.fn(),
  }),
}));

function renderProfilePage() {
  return render(
    <BrowserRouter>
      <ProfilePage />
    </BrowserRouter>,
  );
}

describe("ProfilePage", () => {
  beforeEach(() => {
    mockCallTool.mockClear();
    mockAddToast.mockClear();
    localStorageMock.getItem.mockClear();
    localStorageMock.getItem.mockReturnValue("mock-token");
  });

  describe("Rendering and UI", () => {
    it("should render profile page with title", async () => {
      renderProfilePage();

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Profile" }),
        ).toBeInTheDocument();
      });
    });

    it("should render page subtitle", async () => {
      renderProfilePage();

      await waitFor(() => {
        expect(
          screen.getByText("View your account information"),
        ).toBeInTheDocument();
      });
    });

    it("should render account information section", async () => {
      renderProfilePage();

      await waitFor(() => {
        expect(screen.getByText("Account Information")).toBeInTheDocument();
      });
    });

    it("should display user information", async () => {
      renderProfilePage();

      await waitFor(() => {
        expect(screen.getByText("testuser")).toBeInTheDocument();
        expect(screen.getByText("test@example.com")).toBeInTheDocument();
      });
    });

    it("should display role with full access badge for admin", async () => {
      renderProfilePage();

      await waitFor(() => {
        expect(screen.getByText("Full Access")).toBeInTheDocument();
      });
    });
  });

  describe("Password Change Section", () => {
    it("should render change password section", async () => {
      renderProfilePage();

      await waitFor(() => {
        // Section header uses h6 element
        const changePasswordElements = screen.getAllByText("Change Password");
        expect(changePasswordElements.length).toBeGreaterThanOrEqual(1);
      });
    });

    it("should render password fields", async () => {
      renderProfilePage();

      await waitFor(() => {
        expect(screen.getByLabelText(/current password/i)).toBeInTheDocument();
        // "New Password" and "Confirm New Password" both contain "new password"
        // so we need to be more specific or use getAllByLabelText
        const newPasswordFields = screen.getAllByLabelText(/new password/i);
        expect(newPasswordFields.length).toBeGreaterThanOrEqual(2); // New + Confirm
      });
    });

    it("should render password change button", async () => {
      renderProfilePage();

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: "Change Password" }),
        ).toBeInTheDocument();
      });
    });

    it("should render password requirements helper text", async () => {
      renderProfilePage();

      await waitFor(() => {
        expect(
          screen.getByText(
            /min 12 chars, uppercase, lowercase, number, special character/i,
          ),
        ).toBeInTheDocument();
      });
    });
  });

  describe("Avatar Section", () => {
    it("should render avatar placeholder when no avatar", async () => {
      renderProfilePage();

      await waitFor(() => {
        // Change avatar button should be present (aria-label is used in MUI Tooltip)
        expect(screen.getByLabelText("Change avatar")).toBeInTheDocument();
      });
    });
  });

  describe("i18n Translations", () => {
    it("should use translated page title", async () => {
      renderProfilePage();

      await waitFor(() => {
        expect(
          screen.getByRole("heading", { name: "Profile" }),
        ).toBeInTheDocument();
      });
    });

    it("should use translated section headers", async () => {
      renderProfilePage();

      await waitFor(() => {
        expect(screen.getByText("Account Information")).toBeInTheDocument();
        // "Change Password" appears in both section header and button
        const changePasswordElements = screen.getAllByText("Change Password");
        expect(changePasswordElements.length).toBeGreaterThanOrEqual(1);
      });
    });

    it("should use translated field labels", async () => {
      renderProfilePage();

      await waitFor(() => {
        expect(screen.getByText("Username")).toBeInTheDocument();
        expect(screen.getByText("Email")).toBeInTheDocument();
        expect(screen.getByText("Role")).toBeInTheDocument();
        expect(screen.getByText("Account Created")).toBeInTheDocument();
      });
    });

    it("should use translated button label", async () => {
      renderProfilePage();

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: "Change Password" }),
        ).toBeInTheDocument();
      });
    });
  });
});
