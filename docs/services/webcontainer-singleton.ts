import { WebContainer } from '@webcontainer/api'

/**
 * Singleton WebContainer instance.
 * WebContainer only allows one instance per page, so we share it.
 */

let containerInstance: WebContainer | null = null
let bootPromise: Promise<WebContainer> | null = null
let bootAttempted = false

export async function getWebContainer(): Promise<WebContainer> {
  // Return existing instance
  if (containerInstance) {
    return containerInstance
  }

  // Return in-progress boot
  if (bootPromise) {
    return bootPromise
  }

  // If we already tried to boot and failed, don't try again
  if (bootAttempted) {
    throw new Error('WebContainer boot already attempted. Refresh the page to try again.')
  }

  // Boot new instance
  bootAttempted = true
  try {
    bootPromise = WebContainer.boot()
    containerInstance = await bootPromise
    bootPromise = null
    return containerInstance
  } catch (error) {
    bootPromise = null
    // If error mentions "cloned", it means there's already a WebContainer
    // This can happen with HMR or navigating between pages
    if (error instanceof Error && error.message.includes('clone')) {
      console.warn('WebContainer already exists, page refresh may be needed')
    }
    throw error
  }
}

export function getExistingWebContainer(): WebContainer | null {
  return containerInstance
}

export function isWebContainerBooted(): boolean {
  return containerInstance !== null
}
