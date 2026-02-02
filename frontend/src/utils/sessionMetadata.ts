/**
 * Session Metadata Utilities
 * 
 * Utilities for collecting real session metadata including IP detection,
 * device information, geolocation, and session activity tracking.
 */

export interface DeviceInfo {
  browser: string
  browserVersion: string
  os: string
  osVersion: string
  deviceType: 'desktop' | 'mobile' | 'tablet'
  isMobile: boolean
}

export interface LocationInfo {
  country?: string
  region?: string
  city?: string
  timezone?: string
}

export interface SessionActivity {
  pageViews: number
  keystrokes: number
  mouseClicks: number
  idleTime: number
  lastActiveTab: string
}

export interface RealTimeSessionData {
  sessionId: string
  userId: string
  ipAddress: string
  deviceInfo: DeviceInfo
  locationInfo: LocationInfo
  activity: SessionActivity
  startTime: Date
  lastActivity: Date
  status: 'active' | 'idle' | 'expired'
  isCurrentSession: boolean
}

/**
 * Detect user's real IP address using multiple fallback methods
 */
export async function detectIPAddress(): Promise<string> {
  try {
    // Method 1: Use ipify.org (free, reliable)
    const response = await fetch('https://api.ipify.org?format=json', {
      method: 'GET',
      headers: {
        'Accept': 'application/json'
      }
    })
    
    if (response.ok) {
      const data = await response.json()
      if (data.ip) {
        return data.ip
      }
    }
  } catch (error) {
    console.warn('Primary IP detection failed:', error)
  }

  try {
    // Method 2: Use ipinfo.io as fallback
    const response = await fetch('https://ipinfo.io/json', {
      method: 'GET',
      headers: {
        'Accept': 'application/json'
      }
    })
    
    if (response.ok) {
      const data = await response.json()
      if (data.ip) {
        return data.ip
      }
    }
  } catch (error) {
    console.warn('Fallback IP detection failed:', error)
  }

  // Method 3: WebRTC IP detection (for local networks)
  try {
    const localIP = await detectLocalIP()
    if (localIP) {
      return localIP
    }
  } catch (error) {
    console.warn('WebRTC IP detection failed:', error)
  }

  // Default fallback - return localhost indicator
  return '127.0.0.1'
}

/**
 * Detect local IP using WebRTC
 */
async function detectLocalIP(): Promise<string | null> {
  return new Promise((resolve) => {
    const timeout = setTimeout(() => resolve(null), 1000)
    
    try {
      const pc = new RTCPeerConnection({ iceServers: [] })
      
      pc.createDataChannel('')
      pc.onicecandidate = (e) => {
        if (!e.candidate) return
        
        const candidate = e.candidate.candidate
        const match = candidate.match(/(\d+\.\d+\.\d+\.\d+)/)
        
        if (match && match[1]) {
          clearTimeout(timeout)
          pc.close()
          resolve(match[1])
        }
      }
      
      pc.createOffer().then(offer => pc.setLocalDescription(offer))
    } catch (_error) {
      clearTimeout(timeout)
      resolve(null)
    }
  })
}

/**
 * Get location information based on IP address
 */
export async function getLocationInfo(ipAddress: string): Promise<LocationInfo> {
  try {
    const response = await fetch(`https://ipinfo.io/${ipAddress}/json`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json'
      }
    })
    
    if (response.ok) {
      const data = await response.json()
      return {
        country: data.country,
        region: data.region,
        city: data.city,
        timezone: data.timezone
      }
    }
  } catch (error) {
    console.warn('Location detection failed:', error)
  }

  return {
    country: 'Unknown',
    region: 'Unknown',
    city: 'Unknown',
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
  }
}

/**
 * Parse user agent to extract device information
 */
export function parseDeviceInfo(userAgent: string = navigator.userAgent): DeviceInfo {
  const ua = userAgent.toLowerCase()
  
  // Detect browser
  let browser = 'Unknown'
  let browserVersion = ''
  
  if (ua.includes('chrome') && !ua.includes('edge')) {
    browser = 'Chrome'
    const match = ua.match(/chrome\/(\d+\.?\d*)/)
    browserVersion = match ? match[1] : ''
  } else if (ua.includes('firefox')) {
    browser = 'Firefox'
    const match = ua.match(/firefox\/(\d+\.?\d*)/)
    browserVersion = match ? match[1] : ''
  } else if (ua.includes('safari') && !ua.includes('chrome')) {
    browser = 'Safari'
    const match = ua.match(/version\/(\d+\.?\d*)/)
    browserVersion = match ? match[1] : ''
  } else if (ua.includes('edge')) {
    browser = 'Edge'
    const match = ua.match(/edge\/(\d+\.?\d*)/)
    browserVersion = match ? match[1] : ''
  }
  
  // Detect OS
  let os = 'Unknown'
  let osVersion = ''
  
  if (ua.includes('windows')) {
    os = 'Windows'
    if (ua.includes('windows nt 10')) osVersion = '10/11'
    else if (ua.includes('windows nt 6.3')) osVersion = '8.1'
    else if (ua.includes('windows nt 6.2')) osVersion = '8'
    else if (ua.includes('windows nt 6.1')) osVersion = '7'
  } else if (ua.includes('macintosh') || ua.includes('mac os')) {
    os = 'macOS'
    const match = ua.match(/mac os x (\d+[._]\d+[._]?\d*)/)
    if (match) {
      osVersion = match[1].replace(/_/g, '.')
    }
  } else if (ua.includes('linux')) {
    os = 'Linux'
  } else if (ua.includes('android')) {
    os = 'Android'
    const match = ua.match(/android (\d+\.?\d*)/)
    osVersion = match ? match[1] : ''
  } else if (ua.includes('iphone') || ua.includes('ipad')) {
    os = 'iOS'
    const match = ua.match(/os (\d+_?\d*_?\d*)/)
    if (match) {
      osVersion = match[1].replace(/_/g, '.')
    }
  }
  
  // Detect device type
  const isMobile = /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(ua)
  const isTablet = /ipad|android(?!.*mobile)|tablet/i.test(ua)
  
  let deviceType: 'desktop' | 'mobile' | 'tablet' = 'desktop'
  if (isTablet) {
    deviceType = 'tablet'
  } else if (isMobile) {
    deviceType = 'mobile'
  }
  
  return {
    browser,
    browserVersion,
    os,
    osVersion,
    deviceType,
    isMobile
  }
}

/**
 * Get formatted device string for display
 */
export function formatDeviceString(deviceInfo: DeviceInfo): string {
  const { browser, browserVersion, os, osVersion } = deviceInfo
  
  let result = browser
  if (browserVersion) {
    const majorVersion = browserVersion.split('.')[0]
    result += ` ${majorVersion}`
  }
  
  result += ` on ${os}`
  if (osVersion) {
    result += ` ${osVersion}`
  }
  
  return result
}

/**
 * Calculate session duration in milliseconds
 */
export function getSessionDuration(startTime: Date, endTime: Date = new Date()): number {
  return endTime.getTime() - startTime.getTime()
}

/**
 * Format session duration for display
 */
export function formatSessionDuration(durationMs: number): string {
  const seconds = Math.floor(durationMs / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)
  
  if (days > 0) {
    return `${days}d ${hours % 24}h ${minutes % 60}m`
  } else if (hours > 0) {
    return `${hours}h ${minutes % 60}m`
  } else if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`
  } else {
    return `${seconds}s`
  }
}

/**
 * Initialize session activity tracking
 */
export function createActivityTracker(): SessionActivity {
  return {
    pageViews: 1,
    keystrokes: 0,
    mouseClicks: 0,
    idleTime: 0,
    lastActiveTab: document.title
  }
}

/**
 * Start tracking user activity for session monitoring
 */
export function startActivityTracking(
  activityData: SessionActivity,
  onUpdate: (activity: SessionActivity) => void
): () => void {
  let idleTimer: NodeJS.Timeout | null = null
  let isIdle = false
  
  const resetIdleTimer = () => {
    if (idleTimer) clearTimeout(idleTimer)
    
    if (isIdle) {
      isIdle = false
      onUpdate({ ...activityData })
    }
    
    idleTimer = setTimeout(() => {
      isIdle = true
      onUpdate({ ...activityData })
    }, 5 * 60 * 1000) // 5 minutes idle threshold
  }
  
  const handleActivity = () => {
    resetIdleTimer()
  }
  
  const handleKeypress = () => {
    activityData.keystrokes++
    handleActivity()
  }
  
  const handleClick = () => {
    activityData.mouseClicks++
    handleActivity()
  }
  
  const handleVisibilityChange = () => {
    if (!document.hidden) {
      activityData.pageViews++
      activityData.lastActiveTab = document.title
      handleActivity()
    }
  }
  
  // Add event listeners
  document.addEventListener('keypress', handleKeypress, { passive: true })
  document.addEventListener('click', handleClick, { passive: true })
  document.addEventListener('mousemove', handleActivity, { passive: true })
  document.addEventListener('scroll', handleActivity, { passive: true })
  document.addEventListener('visibilitychange', handleVisibilityChange)
  
  // Start idle tracking
  resetIdleTimer()
  
  // Return cleanup function
  return () => {
    if (idleTimer) clearTimeout(idleTimer)
    document.removeEventListener('keypress', handleKeypress)
    document.removeEventListener('click', handleClick)
    document.removeEventListener('mousemove', handleActivity)
    document.removeEventListener('scroll', handleActivity)
    document.removeEventListener('visibilitychange', handleVisibilityChange)
  }
}