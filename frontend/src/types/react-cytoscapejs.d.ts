declare module "react-cytoscapejs" {
  import type { Core, ElementDefinition, LayoutOptions, StylesheetJson } from "cytoscape";
  import type { CSSProperties, ComponentType } from "react";

  export interface CytoscapeComponentProps {
    elements: ElementDefinition[];
    layout?: LayoutOptions;
    stylesheet?: StylesheetJson;
    style?: CSSProperties;
    className?: string;
    minZoom?: number;
    maxZoom?: number;
    zoom?: number;
    pan?: { x: number; y: number };
    wheelSensitivity?: number;
    cy?: (cy: Core) => void;
  }

  const CytoscapeComponent: ComponentType<CytoscapeComponentProps>;
  export default CytoscapeComponent;
}
