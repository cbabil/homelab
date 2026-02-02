import { Box, Text } from 'ink';
import InkTextInput from 'ink-text-input';
import React, { useState } from 'react';

interface PasswordInputProps {
  label: string;
  onSubmit: (value: string) => void;
  validate?: (value: string) => string | null;
}

export function PasswordInput({ label, onSubmit, validate }: PasswordInputProps) {
  const [value, setValue] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (val: string) => {
    if (validate) {
      const validationError = validate(val);
      if (validationError) {
        setError(validationError);
        return;
      }
    }
    setError(null);
    onSubmit(val);
  };

  return (
    <Box flexDirection="column">
      <Box>
        <Text color="cyan">? </Text>
        <Text>{label}: </Text>
        <InkTextInput
          value={value}
          onChange={(val) => {
            setValue(val);
            setError(null);
          }}
          onSubmit={handleSubmit}
          mask="*"
        />
      </Box>
      {error && (
        <Box marginLeft={2}>
          <Text color="red">{error}</Text>
        </Box>
      )}
    </Box>
  );
}
