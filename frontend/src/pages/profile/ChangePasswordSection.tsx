/**
 * Change Password Section Component
 *
 * Form for changing user password with validation and visibility toggles.
 */

import React from "react";
import { Eye, EyeOff, Check } from "lucide-react";
import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import Typography from "@mui/material/Typography";
import TextField from "@mui/material/TextField";
import IconButton from "@mui/material/IconButton";
import { Button } from "@/components/ui/Button";
import { useTranslation } from "react-i18next";

interface ChangePasswordSectionProps {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
  showCurrentPassword: boolean;
  showNewPassword: boolean;
  showConfirmPassword: boolean;
  isChangingPassword: boolean;
  isConnected: boolean;
  onCurrentPasswordChange: (value: string) => void;
  onNewPasswordChange: (value: string) => void;
  onConfirmPasswordChange: (value: string) => void;
  onToggleCurrentPassword: () => void;
  onToggleNewPassword: () => void;
  onToggleConfirmPassword: () => void;
  onSubmit: (e: React.FormEvent) => void;
}

export function ChangePasswordSection({
  currentPassword,
  newPassword,
  confirmPassword,
  showCurrentPassword,
  showNewPassword,
  showConfirmPassword,
  isChangingPassword,
  isConnected,
  onCurrentPasswordChange,
  onNewPasswordChange,
  onConfirmPasswordChange,
  onToggleCurrentPassword,
  onToggleNewPassword,
  onToggleConfirmPassword,
  onSubmit,
}: ChangePasswordSectionProps) {
  const { t } = useTranslation();

  const passwordsMatch =
    confirmPassword !== "" && confirmPassword === newPassword;
  const passwordsDontMatch =
    confirmPassword !== "" && confirmPassword !== newPassword;

  return (
    <Card sx={{ p: 2 }}>
      <Typography
        variant="subtitle2"
        fontWeight={600}
        color="primary"
        sx={{ mb: 2 }}
      >
        {t("profile.changePassword")}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t("profile.passwordChangeDescription")}
      </Typography>

      <Box
        component="form"
        onSubmit={onSubmit}
        sx={{ display: "flex", flexDirection: "column", gap: 2, maxWidth: 480 }}
      >
        <TextField
          label={t("profile.currentPassword")}
          type={showCurrentPassword ? "text" : "password"}
          value={currentPassword}
          onChange={(e) => onCurrentPasswordChange(e.target.value)}
          fullWidth
          size="small"
          required
          InputProps={{
            endAdornment: (
              <IconButton
                size="small"
                onClick={onToggleCurrentPassword}
                edge="end"
              >
                {showCurrentPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </IconButton>
            ),
          }}
        />

        <TextField
          label={t("profile.newPassword")}
          type={showNewPassword ? "text" : "password"}
          value={newPassword}
          onChange={(e) => onNewPasswordChange(e.target.value)}
          fullWidth
          size="small"
          required
          helperText={t("profile.passwordRequirements")}
          InputProps={{
            endAdornment: (
              <IconButton size="small" onClick={onToggleNewPassword} edge="end">
                {showNewPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </IconButton>
            ),
          }}
        />

        <TextField
          label={t("profile.confirmNewPassword")}
          type={showConfirmPassword ? "text" : "password"}
          value={confirmPassword}
          onChange={(e) => onConfirmPasswordChange(e.target.value)}
          fullWidth
          size="small"
          required
          error={passwordsDontMatch}
          helperText={
            passwordsDontMatch ? t("profile.passwordsDoNotMatch") : ""
          }
          InputProps={{
            endAdornment: passwordsMatch ? (
              <Check size={16} style={{ color: "#10b981" }} />
            ) : (
              <IconButton
                size="small"
                onClick={onToggleConfirmPassword}
                edge="end"
              >
                {showConfirmPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </IconButton>
            ),
          }}
        />

        <Button
          type="submit"
          variant="primary"
          size="sm"
          disabled={
            !currentPassword || !newPassword || !confirmPassword || !isConnected
          }
          loading={isChangingPassword}
        >
          {t("profile.changePasswordButton")}
        </Button>
      </Box>
    </Card>
  );
}
