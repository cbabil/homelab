/**
 * Privacy Policy Content Component
 * 
 * Content sections for the Privacy Policy page.
 */

export function PrivacyPolicyContent() {
  return (
    <div className="prose prose-sm max-w-none text-foreground space-y-6">
      <p><strong>Last updated:</strong> {new Date().toLocaleDateString()}</p>
      
      <section>
        <h2 className="text-xl font-semibold mb-3">1. Information We Collect</h2>
        <p>As a self-hosted application, all data remains on your infrastructure. We collect:</p>
        <ul className="list-disc ml-6 space-y-2">
          <li><strong>Account Information:</strong> Username, email address, and encrypted passwords</li>
          <li><strong>Server Connections:</strong> Hostnames, connection credentials (encrypted)</li>
          <li><strong>Application Logs:</strong> Access logs and error logs for troubleshooting</li>
          <li><strong>Session Data:</strong> Authentication tokens and session management data</li>
        </ul>
      </section>
      
      <section>
        <h2 className="text-xl font-semibold mb-3">2. How We Use Your Information</h2>
        <p>Your information is used solely to:</p>
        <ul className="list-disc ml-6 space-y-2">
          <li>Authenticate and authorize access to your homelab</li>
          <li>Manage server connections and infrastructure</li>
          <li>Provide monitoring and administrative capabilities</li>
          <li>Maintain application security and functionality</li>
        </ul>
      </section>
      
      <section>
        <h2 className="text-xl font-semibold mb-3">3. Data Storage and Security</h2>
        <p>All data is stored locally on your infrastructure with the following protections:</p>
        <ul className="list-disc ml-6 space-y-2">
          <li>Passwords are hashed using industry-standard algorithms</li>
          <li>Sensitive credentials are encrypted at rest</li>
          <li>Session tokens use secure JWT standards</li>
          <li>Database access is protected by authentication</li>
        </ul>
      </section>
      
      <section>
        <h2 className="text-xl font-semibold mb-3">4. Data Sharing</h2>
        <p>
          <strong>We do not share your data with third parties.</strong> This application is entirely 
          self-contained and does not transmit data to external services unless explicitly configured 
          by you (e.g., monitoring integrations).
        </p>
      </section>
      
      <section>
        <h2 className="text-xl font-semibold mb-3">5. Data Retention</h2>
        <p>You have full control over data retention. Data is kept until you:</p>
        <ul className="list-disc ml-6 space-y-2">
          <li>Delete your account</li>
          <li>Remove server connections</li>
          <li>Uninstall the application</li>
        </ul>
      </section>
      
      <section>
        <h2 className="text-xl font-semibold mb-3">6. Your Rights</h2>
        <p>As the data owner, you have the right to:</p>
        <ul className="list-disc ml-6 space-y-2">
          <li>Access all your stored data</li>
          <li>Modify or delete your information</li>
          <li>Export your data</li>
          <li>Control data sharing preferences</li>
        </ul>
      </section>
      
      <section>
        <h2 className="text-xl font-semibold mb-3">7. Contact Information</h2>
        <p>
          For privacy-related questions about this self-hosted application, 
          consult the application documentation or repository.
        </p>
      </section>
    </div>
  )
}