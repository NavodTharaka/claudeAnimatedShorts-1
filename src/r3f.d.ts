import "react";
// @types/react 19 reads intrinsic elements from React.JSX (no global JSX), so augment the react module.
declare module "react" { namespace JSX { interface IntrinsicElements { primitive: any } } }
export {};
