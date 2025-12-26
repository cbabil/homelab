/**
 * Privacy Policy Page
 * 
 * Standalone page for Privacy Policy, designed to open in popup windows.
 */

import { PrivacyPolicyContent } from '@/components/legal/PrivacyPolicyContent'

export function PrivacyPolicyPage() {
  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-4xl mx-auto">
        <div className="bg-card rounded-lg border shadow-sm p-8">
          <h1 className="text-3xl font-bold text-foreground mb-6">Privacy Policy</h1>
          
          <PrivacyPolicyContent />
          
          <div className="mt-8 pt-6 border-t text-center">
            <button
              onClick={() => window.close()}
              className="bg-primary text-primary-foreground hover:bg-primary/90 px-6 py-2 rounded-md transition-colors"
            >
              Close Window
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}