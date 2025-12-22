import { WebContainer } from '@webcontainer/api'

/**
 * Singleton WebContainer instance.
 * WebContainer only allows one instance per page, so we share it.
 */

let containerInstance: WebContainer | null = null
let bootPromise: Promise<WebContainer> | null = null

export async function getWebContainer(): Promise<WebContainer> {
  // Return existing instance
  if (containerInstance) {
    return containerInstance
  }

  // Return in-progress boot
  if (bootPromise) {
    return bootPromise
  }

  // Boot new instance
  bootPromise = WebContainer.boot()
  containerInstance = await bootPromise
  bootPromise = null

  return containerInstance
}

export function getExistingWebContainer(): WebContainer | null {
  return containerInstance
}
