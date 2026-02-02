import { Box, Text } from 'ink';
import InkTextInput from 'ink-text-input';
import React, { useState } from 'react';

interface TextInputProps {
  label: string;
  onSubmit: (value: string) => void;
  placeholder?: string;
  defaultValue?: string;
  validate?: (value: string) => string | null;
}

export function TextInput({
  label,
  onSubmit,
  placeholder,
  defaultValue = '',
  validate,
}: TextInputProps) {
  const [value, setValue] = useState(defaultValue);
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
          placeholder={placeholder}
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
