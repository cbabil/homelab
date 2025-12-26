/**
 * Terms of Service Page
 * 
 * Standalone page for Terms of Service, designed to open in popup windows.
 */

export function TermsOfServicePage() {
  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-4xl mx-auto">
        <div className="bg-card rounded-lg border shadow-sm p-8">
          <h1 className="text-3xl font-bold text-foreground mb-6">Terms of Service</h1>
          
          <div className="prose prose-sm max-w-none text-foreground space-y-6">
            <p><strong>Last updated:</strong> {new Date().toLocaleDateString()}</p>
            
            <section>
              <h2 className="text-xl font-semibold mb-3">1. Acceptance of Terms</h2>
              <p>
                By accessing and using the Homelab Assistant application, you accept and agree to be bound 
                by the terms and provision of this agreement.
              </p>
            </section>
            
            <section>
              <h2 className="text-xl font-semibold mb-3">2. Service Description</h2>
              <p>
                Homelab Assistant is a self-hosted application for managing home laboratory infrastructure, 
                including server connections, service monitoring, and system administration.
              </p>
            </section>
            
            <section>
              <h2 className="text-xl font-semibold mb-3">3. User Responsibilities</h2>
              <ul className="list-disc ml-6 space-y-2">
                <li>You are responsible for maintaining the confidentiality of your account credentials</li>
                <li>You agree to use the service only for lawful purposes</li>
                <li>You are responsible for securing your homelab infrastructure</li>
                <li>You agree not to attempt to breach security measures</li>
              </ul>
            </section>
            
            <section>
              <h2 className="text-xl font-semibold mb-3">4. Data and Privacy</h2>
              <p>
                This application is self-hosted on your infrastructure. You maintain full control over 
                your data. No data is transmitted to external services without your explicit configuration.
              </p>
            </section>
            
            <section>
              <h2 className="text-xl font-semibold mb-3">5. Security Considerations</h2>
              <p>
                You acknowledge that this application provides access to your infrastructure and agree to:
              </p>
              <ul className="list-disc ml-6 space-y-2">
                <li>Use strong, unique passwords</li>
                <li>Keep the application updated</li>
                <li>Monitor access logs</li>
                <li>Report security issues responsibly</li>
              </ul>
            </section>
            
            <section>
              <h2 className="text-xl font-semibold mb-3">6. Limitation of Liability</h2>
              <p>
                This software is provided "as is" without warranty. The developers are not liable for 
                any damages arising from the use of this application.
              </p>
            </section>
            
            <section>
              <h2 className="text-xl font-semibold mb-3">7. Changes to Terms</h2>
              <p>
                These terms may be updated periodically. Continued use of the application constitutes 
                acceptance of updated terms.
              </p>
            </section>
            
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
    </div>
  )
}