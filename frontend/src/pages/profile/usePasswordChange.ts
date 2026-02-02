/**
 * Password Change Hook
 *
 * Handles password change form state and submission logic.
 */

import React, { useState } from "react";
import { useMCP } from "@/providers/MCPProvider";
import { useToast } from "@/components/ui/Toast";
import { useTranslation } from "react-i18next";
import { AUTH_STORAGE_KEYS } from "@/types/auth";
import type { ChangePasswordResponse } from "./types";

function getToken(): string | null {
  return (
    localStorage.getItem(AUTH_STORAGE_KEYS.TOKEN) ||
    sessionStorage.getItem(AUTH_STORAGE_KEYS.TOKEN)
  );
}

function validatePasswordComplexity(
  password: string,
  t: (key: string) => string,
) {
  const hasUpper = /[A-Z]/.test(password);
  const hasLower = /[a-z]/.test(password);
  const hasDigit = /\d/.test(password);
  const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(password);

  if (!hasUpper || !hasLower || !hasDigit || !hasSpecial) {
    const missing = [];
    if (!hasUpper) missing.push(t("profile.uppercaseLetter"));
    if (!hasLower) missing.push(t("profile.lowercaseLetter"));
    if (!hasDigit) missing.push(t("profile.number"));
    if (!hasSpecial) missing.push(t("profile.specialCharacter"));
    return { valid: false, missing };
  }

  return { valid: true, missing: [] };
}

export function usePasswordChange() {
  const { t } = useTranslation();
  const { client, isConnected } = useMCP();
  const { addToast } = useToast();

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isChangingPassword, setIsChangingPassword] = useState(false);

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!isConnected) {
      addToast({
        type: "error",
        title: t("profile.notConnected"),
        message: t("profile.waitForBackendConnection"),
      });
      return;
    }

    if (newPassword !== confirmPassword) {
      addToast({
        type: "error",
        title: t("profile.passwordsDoNotMatch"),
        message: t("profile.passwordsDoNotMatchMessage"),
      });
      return;
    }

    if (newPassword.length < 12) {
      addToast({
        type: "error",
        title: t("profile.passwordTooShort"),
        message: t("profile.passwordTooShortMessage"),
      });
      return;
    }

    const { valid, missing } = validatePasswordComplexity(newPassword, t);
    if (!valid) {
      addToast({
        type: "error",
        title: t("profile.passwordRequirementsNotMet"),
        message: t("profile.passwordRequirementsNotMetMessage", {
          missing: missing.join(", "),
        }),
      });
      return;
    }

    setIsChangingPassword(true);

    try {
      const token = getToken();
      if (!token) {
        addToast({
          type: "error",
          title: t("profile.sessionExpired"),
          message: t("profile.sessionExpiredMessage"),
        });
        return;
      }

      const response = await client.callTool<ChangePasswordResponse>(
        "change_password",
        { token, current_password: currentPassword, new_password: newPassword },
      );
      const result = response.data as ChangePasswordResponse | undefined;

      if (response.success && result?.success) {
        addToast({
          type: "success",
          title: t("profile.passwordChangedSuccess"),
          message: t("profile.passwordChangedSuccessMessage"),
        });
        setCurrentPassword("");
        setNewPassword("");
        setConfirmPassword("");
      } else {
        handlePasswordChangeError(result?.error, result?.message);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : t("common.error");
      addToast({
        type: "error",
        title: t("profile.passwordChangeFailed"),
        message,
      });
    } finally {
      setIsChangingPassword(false);
    }
  };

  const handlePasswordChangeError = (error?: string, message?: string) => {
    const errorCode = error || "UNKNOWN_ERROR";
    const errorMessage = message || t("profile.passwordChangeFailed");

    if (errorCode === "RATE_LIMITED") {
      addToast({
        type: "error",
        title: t("profile.accountTemporarilyLocked"),
        message: errorMessage,
      });
    } else if (errorCode === "INVALID_CURRENT_PASSWORD") {
      addToast({
        type: "error",
        title: t("profile.incorrectPassword"),
        message: errorMessage,
      });
    } else if (errorCode === "WEAK_PASSWORD") {
      addToast({
        type: "error",
        title: t("profile.weakPassword"),
        message: errorMessage,
      });
    } else if (errorCode === "INVALID_TOKEN") {
      addToast({
        type: "error",
        title: t("profile.sessionExpired"),
        message: t("profile.sessionExpiredMessage"),
      });
    } else {
      addToast({
        type: "error",
        title: t("profile.passwordChangeFailed"),
        message: errorMessage,
      });
    }
  };

  return {
    currentPassword,
    setCurrentPassword,
    newPassword,
    setNewPassword,
    confirmPassword,
    setConfirmPassword,
    showCurrentPassword,
    setShowCurrentPassword,
    showNewPassword,
    setShowNewPassword,
    showConfirmPassword,
    setShowConfirmPassword,
    isChangingPassword,
    isConnected,
    handlePasswordChange,
  };
}
