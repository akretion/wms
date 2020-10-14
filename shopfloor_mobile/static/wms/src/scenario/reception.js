import {ScenarioBaseMixin} from "./mixins.js";
import {process_registry} from "../services/process_registry.js";

const Reception = {
    mixins: [ScenarioBaseMixin],
    template: `
        <Screen :screen_info="screen_info">
            Hello, Reception here
        </Screen>
    `
}

process_registry.add("reception", Reception);

export default Reception;
