import die from "./definitions/die";
import dosingMaterial from "./definitions/dosingMaterial";
import extruder from "./definitions/extruder";
import generalEvent from "./definitions/generalEvent";
import granulator from "./definitions/granulator";
import quality from "./definitions/quality";
import screenChanger from "./definitions/screenChanger";
import waterBox from "./definitions/waterBox";

export const FORM_DEFINITIONS = {
  dosing_material: dosingMaterial,
  extruder,
  screen_changer: screenChanger,
  die,
  water_box: waterBox,
  granulator,
  quality,
  general_event: generalEvent,
};

export const FORM_DEFINITION_IDS = Object.keys(FORM_DEFINITIONS);

export function getFormDefinition(categoryId) {
  return FORM_DEFINITIONS[categoryId] ?? null;
}

/** Flat field lookup for a category, keyed by field id. */
export function getFormFieldMap(categoryId) {
  const definition = getFormDefinition(categoryId);
  if (!definition) {
    return {};
  }
  return Object.fromEntries(definition.fields.map((field) => [field.id, field]));
}

export {
  FORM_CATEGORIES,
  FORM_CATEGORY_MAP,
  getCategory,
  getCategoryByPath,
} from "./categories";
