/**
 * Basic Form Fields Component
 *
 * Username field for registration form.
 */

import TextField from '@mui/material/TextField'
import InputAdornment from '@mui/material/InputAdornment'
import { Person } from '@mui/icons-material'
import { RegistrationFormState } from '@/types/auth'
import { FormHandlers } from '@/utils/registrationFormHandlers'

interface BasicFormFieldsProps {
  formState: RegistrationFormState
  formHandlers: FormHandlers
}

export function BasicFormFields({
  formState,
  formHandlers
}: BasicFormFieldsProps) {
  return (
    <TextField
      id="reg-username"
      label="Username"
      type="text"
      autoComplete="username"
      required
      fullWidth
      placeholder="Enter username"
      value={formState.username.value}
      onChange={(e) => formHandlers.handleInputChange('username', e.target.value)}
      disabled={formState.isSubmitting}
      error={!!formState.username.error}
      helperText={formState.username.error}
      slotProps={{
        input: {
          startAdornment: (
            <InputAdornment position="start">
              <Person color="action" />
            </InputAdornment>
          ),
        },
      }}
      sx={{ mb: 2 }}
    />
  )
}