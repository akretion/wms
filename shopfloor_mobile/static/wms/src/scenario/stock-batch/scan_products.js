Vue.component("stock-batch-scan-products", {
    template: `
    <batch-move-line
        :moveLines="state.data.move_lines"
        :fields="state.fields"
        :lastScanned="lastScanned"
        :selectedLocation="selectedLocation"
        :currentLocation="currentLocation"
        :lastPickedLine="lastPickedLine"
        @action="state.actionStockOut"
        />
    `,
});
