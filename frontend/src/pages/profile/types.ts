/**
 * Profile Page Types
 */

export interface UserProfile {
  id: string;
  username: string;
  email?: string;
  role: "admin" | "user";
  is_active: boolean;
  last_login?: string;
  created_at?: string;
  updated_at?: string;
  avatar?: string | null;
}

export interface GetCurrentUserResponse {
  success: boolean;
  data?: {
    user: UserProfile;
  };
  message?: string;
  error?: string;
}

export interface ChangePasswordResponse {
  success: boolean;
  message?: string;
  error?: string;
}

export interface UpdateAvatarResponse {
  success: boolean;
  message?: string;
  error?: string;
}

export const MAX_AVATAR_SIZE = 500 * 1024; // 500KB
