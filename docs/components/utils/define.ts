/**
 * Register a custom element if not already defined.
 */
export function define(
  tagName: string,
  constructor: CustomElementConstructor
): void {
  if (!customElements.get(tagName)) {
    customElements.define(tagName, constructor)
  }
}
