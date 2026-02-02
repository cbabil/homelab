/**
 * MUI Component Overrides Index
 *
 * Combines all component overrides into a single function.
 */

import type { ThemeOptions } from '@mui/material/styles'
import { getButtonOverrides } from './buttonOverrides'
import { getInputOverrides } from './inputOverrides'
import { getSurfaceOverrides } from './surfaceOverrides'
import { getMiscOverrides } from './miscOverrides'

type ThemeMode = 'light' | 'dark'

export const getComponentOverrides = (
  mode: ThemeMode
): ThemeOptions['components'] => ({
  ...getButtonOverrides(mode),
  ...getInputOverrides(),
  ...getSurfaceOverrides(mode),
  ...getMiscOverrides(mode),
})
