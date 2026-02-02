/**
 * Add Repository Modal Component
 *
 * Modal dialog for adding new marketplace repositories.
 */

import { useState } from 'react'
import {
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Select,
  MenuItem,
  FormControl,
  Alert,
  Box,
  Typography
} from '@mui/material'
import { useTranslation } from 'react-i18next'
import { Button } from '@/components/ui/Button'
import type { RepoType } from '@/types/marketplace'

export interface AddRepoModalProps {
  isOpen: boolean
  onClose: () => void
  onAdd: (name: string, url: string, repoType: RepoType, branch: string) => Promise<void>
}

export function AddRepoModal({ isOpen, onClose, onAdd }: AddRepoModalProps) {
  const { t } = useTranslation()
  const [name, setName] = useState('')
  const [url, setUrl] = useState('')
  const [repoType, setRepoType] = useState<RepoType>('community')
  const [branch, setBranch] = useState('main')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const repoTypeOptions = [
    { label: t('marketplace.repoTypes.official'), value: 'official' },
    { label: t('marketplace.repoTypes.community'), value: 'community' },
    { label: t('marketplace.repoTypes.personal'), value: 'personal' }
  ]

  const handleSubmit = async () => {
    if (!name || !url) return

    setIsSubmitting(true)
    setError(null)

    try {
      await onAdd(name, url, repoType, branch)
      setName('')
      setUrl('')
      setRepoType('community')
      setBranch('main')
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : t('marketplace.errors.addFailed'))
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleClose = () => {
    setName('')
    setUrl('')
    setRepoType('community')
    setBranch('main')
    setError(null)
    onClose()
  }

  return (
    <Dialog open={isOpen} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>{t('marketplace.addRepository')}</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
          <Box>
            <Typography component="label" sx={{ display: 'block', fontSize: '0.875rem', fontWeight: 500, mb: 0.75 }}>
              {t('marketplace.repoName')}
            </Typography>
            <TextField
              size="small"
              fullWidth
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={t('marketplace.repoNamePlaceholder')}
            />
          </Box>

          <Box>
            <Typography component="label" sx={{ display: 'block', fontSize: '0.875rem', fontWeight: 500, mb: 0.75 }}>
              {t('marketplace.repoUrl')}
            </Typography>
            <TextField
              size="small"
              fullWidth
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://github.com/user/repo"
            />
          </Box>

          <Box>
            <Typography component="label" sx={{ display: 'block', fontSize: '0.875rem', fontWeight: 500, mb: 0.75 }}>
              {t('marketplace.repoType')}
            </Typography>
            <FormControl size="small" fullWidth>
              <Select
                value={repoType}
                onChange={(e) => setRepoType(e.target.value as RepoType)}
              >
                {repoTypeOptions.map((opt) => (
                  <MenuItem key={opt.value} value={opt.value}>{opt.label}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>

          <Box>
            <Typography component="label" sx={{ display: 'block', fontSize: '0.875rem', fontWeight: 500, mb: 0.75 }}>
              {t('marketplace.branch')}
            </Typography>
            <TextField
              size="small"
              fullWidth
              value={branch}
              onChange={(e) => setBranch(e.target.value)}
              placeholder="main"
            />
          </Box>

          {error && (
            <Alert severity="error">{error}</Alert>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button variant="ghost" onClick={handleClose} disabled={isSubmitting}>
          {t('common.cancel')}
        </Button>
        <Button variant="primary" onClick={handleSubmit} disabled={!name || !url} loading={isSubmitting}>
          {t('marketplace.addRepository')}
        </Button>
      </DialogActions>
    </Dialog>
  )
}
