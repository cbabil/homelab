/**
 * Server Basic Fields Component
 * 
 * Handles basic server connection information input fields.
 */


interface ServerBasicFieldsProps {
  formData: {
    name: string
    host: string
    port: number
    username: string
  }
  onInputChange: (field: string, value: string | number) => void
}

export function ServerBasicFields({ 
  formData, 
  onInputChange 
}: ServerBasicFieldsProps) {
  return (
    <>
      <div>
        <label className="block text-sm font-medium mb-1">Server Name</label>
        <input
          type="text"
          value={formData.name}
          onChange={(e) => onInputChange('name', e.target.value)}
          className="w-full px-3 py-2 border border-input rounded-lg bg-background focus:outline-none"
          placeholder="My Server"
          required
        />
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div className="col-span-2">
          <label className="block text-sm font-medium mb-1">Hostname/IP</label>
          <input
            type="text"
            value={formData.host}
            onChange={(e) => onInputChange('host', e.target.value)}
            className="w-full px-3 py-2 border border-input rounded-lg bg-background focus:outline-none"
            placeholder="192.168.1.100"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Port</label>
          <input
            type="number"
            value={formData.port}
            onChange={(e) => onInputChange('port', parseInt(e.target.value))}
            className="w-full px-3 py-2 border border-input rounded-lg bg-background focus:outline-none"
            min="1"
            max="65535"
            required
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Username</label>
        <input
          type="text"
          value={formData.username}
          onChange={(e) => onInputChange('username', e.target.value)}
          className="w-full px-3 py-2 border border-input rounded-lg bg-background focus:outline-none"
          placeholder="admin"
          required
        />
      </div>
    </>
  )
}