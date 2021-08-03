<template>
    <v-app>
        <v-app-bar app color="blue-grey lighten-5" height="128" hide-on-scroll>
            <div class="d-flex align-center">
                <v-img
                    alt="Logo"
                    class="shrink mr-2"
                    contain
                    :src="getPath('Icon_128.png')"
                    transition="scale-transition"
                    width="128"
                />
            </div>
            <v-toolbar-title>Teh Hash BOM</v-toolbar-title>

            <v-spacer></v-spacer>
        </v-app-bar>

        <v-main class="pb-5">
            <BomTable />
        </v-main>

        <v-footer>
            <v-col class="text-center" cols="12">
                {{ new Date().toLocaleDateString() }}
                {{ new Date().toLocaleTimeString() }} — Teh Hash BOM
            </v-col>
        </v-footer>
    </v-app>
</template>

<script lang="ts">
import { Component, Vue } from "vue-property-decorator";

import BomTable from "./components/BomTable.vue";

declare var asset_dirrectory: string;

@Component({
    components: { BomTable },
})
export default class App extends Vue {
    getPath(name: string): string {
        if (typeof asset_dirrectory === "undefined") {
            return name;
        }

        return asset_dirrectory + "/" + name;
    }
}

// export default Vue.extend({
//     name: "App",

//     components: {
//         BomTable,
//     },

//     data: () => ({
//         //
//     }),
// });
</script>
