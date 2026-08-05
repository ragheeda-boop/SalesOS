declare module "jest-axe" {
  import { type AxeResults } from "axe-core";
  export function axe(html: HTMLElement): Promise<AxeResults>;
  export const toHaveNoViolations: {
    toHaveNoViolations(this: jest.MatcherContext, received: AxeResults): jest.CustomMatcherResult;
  };
}
