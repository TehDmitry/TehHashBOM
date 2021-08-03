<template>
    <v-container>
        <h3 class="title py-10">BOM Items</h3>
        <v-row class="text-center">
            <v-col cols="12">
                <v-data-table
                    :headers="headersBOM"
                    :items="getBomItems()"
                    class="elevation-1"
                    item-key="id"
                    disable-pagination
                    hide-default-footer
                >
                    <template v-slot:item.image="{ item }">
                        <div class="p-2">
                            <v-img
                                contain
                                :src="item.image"
                                :alt="item.name"
                                max-height="128"
                                max-width="128"
                            ></v-img>
                        </div>
                    </template>
                </v-data-table>
            </v-col>
        </v-row>

        <h3 class="title py-10">Profiles</h3>
        <v-row class="text-center">
            <v-col cols="12">
                <v-data-table
                    v-model="selectedItems"
                    :headers="headers"
                    :items="getProfiles(-1)"
                    class="elevation-1 mb-5"
                    item-key="id"
                    show-select
                    disable-pagination
                    hide-default-footer
                >
                    <template v-slot:item.image="{ item }">
                        <div class="p-2">
                            <v-img
                                contain
                                :src="item.image"
                                :alt="item.name"
                                max-height="128"
                                max-width="128"
                            ></v-img>
                        </div>
                    </template>
                </v-data-table>
                <div class="text-center pt-2">
                    <v-btn color="primary" class="mr-2" @click="addToLayout">
                        Add selected to layout
                    </v-btn>
                </div>
            </v-col>
        </v-row>

        <div v-for="(entity, index) in profileLayouts" :key="`entity-${index}`">
            <h3 class="subtitle-1 py-5">Profile Layout</h3>

            <v-row>
                <v-col cols="12">
                    <v-data-table
                        :headers="headers"
                        :items="getProfiles(index)"
                        class="elevation-1"
                        item-key="id"
                        disable-pagination
                        hide-default-footer
                    >
                        <template v-slot:item.image="{ item }">
                            <div class="p-2">
                                <v-img
                                    contain
                                    :src="item.image"
                                    :alt="item.name"
                                    max-height="128"
                                    max-width="128"
                                ></v-img>
                            </div>
                        </template>

                        <template v-slot:item.layout_index="{ item }">
                            <v-btn
                                color="primary"
                                class="mr-2"
                                @click="clearLayout(item)"
                            >
                                Delete from layout
                            </v-btn>
                        </template>
                    </v-data-table>
                </v-col>
            </v-row>
            <v-row justify="center">
                <v-col cols="12" sm="10" md="8" lg="6">
                    <v-card ref="form">
                        <v-container fluid>
                            <v-row>
                                <v-col cols="12" sm="6">
                                    <v-card-text>
                                        <v-text-field
                                            v-model="entity.max_length"
                                            label="raw bar length"
                                        ></v-text-field>
                                    </v-card-text>
                                </v-col>

                                <v-col cols="12" sm="6">
                                    <v-card-text>
                                        <v-text-field
                                            v-model="entity.spacing"
                                            label="cut with"
                                        ></v-text-field>
                                    </v-card-text>
                                </v-col>
                            </v-row>
                        </v-container>

                        <v-divider class="mt-2"></v-divider>
                        <v-card-actions>
                            <v-spacer></v-spacer>
                            <v-btn
                                color="primary"
                                text
                                @click="
                                    recalculateLayout(
                                        index,
                                        entity.max_length,
                                        entity.spacing
                                    )
                                "
                            >
                                Recalculate cut list
                            </v-btn>
                        </v-card-actions>
                    </v-card>
                </v-col>
            </v-row>

            <v-row justify="center" class="pb-5">
                <v-col cols="12" sm="12" md="12" lg="12">
                    <v-card
                        class="pa-2"
                        outlined
                        v-if="
                            getLayoutBars(index).length > 0 ||
                            getUnfitedChunks(index).length > 0
                        "
                    >
                        <v-card-title> Cut list </v-card-title>

                        <v-alert
                            v-if="getUnfitedChunks(index).length > 0"
                            type="error"
                        >
                            Unfited Chunks:

                            <v-chip
                                v-for="(uchunk, chunkindex) in getUnfitedChunks(
                                    index
                                )"
                                :key="`UnfitedChunk-${chunkindex}`"
                            >
                                {{ uchunk }}
                            </v-chip>
                        </v-alert>

                        <div
                            v-for="(rawBar, layindex) in getLayoutBars(index)"
                            :key="`lay-${layindex}`"
                        >
                            <v-card-subtitle>
                                #{{ layindex + 1 }} len:{{ rawBar.length }}
                            </v-card-subtitle>
                            <v-card-text>
                                <table
                                    border="0"
                                    class="blue-grey darken-1"
                                    style="width: 100%"
                                >
                                    <tr>
                                        <td
                                            :class="
                                                chunk < 10
                                                    ? 'red darken-2'
                                                    : 'amber'
                                            "
                                            :style="{
                                                width:
                                                    chunk >= 10
                                                        ? (chunk * 100) /
                                                              rawBar.length +
                                                          '%'
                                                        : '5px',
                                                'text-align': 'center',
                                                height: '25px',
                                                'min-width': '10px',
                                            }"
                                            v-for="(
                                                chunk, chunkindex
                                            ) in rawBar.chunks"
                                            :key="`chunk-${chunkindex}`"
                                        >
                                            <strong>{{ chunk }}</strong>
                                        </td>

                                        <td
                                            class="blue-grey lighten-3"
                                            :style="{
                                                width:
                                                    (rawBar.lengthRemaining() *
                                                        100) /
                                                        rawBar.length -
                                                    1 +
                                                    '%',
                                                'text-align': 'center',
                                                height: '25px',
                                            }"
                                        >
                                            <strong>
                                                {{
                                                    Math.round(
                                                        (rawBar.lengthRemaining() +
                                                            Number.EPSILON) *
                                                            100
                                                    ) / 100
                                                }}
                                            </strong>
                                        </td>
                                    </tr>
                                </table>
                            </v-card-text>
                        </div>
                    </v-card>
                </v-col>
            </v-row>
        </div>
    </v-container>
</template>

<script lang="ts">
import { Component, Prop, Vue } from "vue-property-decorator";
import BomItemFromFusion from "@/models/BomItemFromFusion";
import BomProfileLayout from "@/models/BomProfileLayout";
import Material1D from "@/models/Material1D";

declare var generatedBOMTable: any;
declare var generatedBeamTable: any;

@Component
export default class BomTable extends Vue {
    @Prop() private msg!: string;

    defalut_max_length = 3000;
    defalut_spacing = 2;

    //@Prop()
    headersBOM = [
        { text: "Image", value: "image", sortable: false },
        {
            text: "Name",
            align: "start",
            value: "name",
        },
        { text: "instances", value: "instances" },
    ];

    headers = [
        { text: "Image", value: "image", sortable: false },
        {
            text: "Name",
            align: "start",
            value: "name",
        },
        { text: "instances", value: "instances" },
        { text: "size", value: "profile_size" },
        { text: "length", value: "profile_length" },
        { text: "layout_index", value: "layout_index" },
    ];

    //@Prop()
    selectedItems: Array<BomItemFromFusion> = [];
    //@Prop()
    bomItems: Array<BomItemFromFusion> = [];
    profileLayouts: Array<BomProfileLayout> = [];

    getProfiles(layoutIndex: number): Array<BomItemFromFusion> {
        return this.bomItems.filter(
            (el) => el.is_profile && el.layout_index == layoutIndex
        );
    }

    getBomItems(): Array<BomItemFromFusion> {
        return this.bomItems.filter((el) => !el.is_profile);
    }

    getLayoutBars(layoutIndex: number): Array<Material1D> {
        console.log("getLayoutBars", layoutIndex);
        return this.profileLayouts[layoutIndex].getRawBars();
    }

    getUnfitedChunks(layoutIndex: number): Array<number> {
        return this.profileLayouts[layoutIndex].getUnfitedChunks();
    }

    clearLayout(item: BomItemFromFusion): void {
        item.layout_index = -1;
    }

    recalculateLayout(
        index: number,
        max_length: number,
        spacing: number
    ): void {
        console.log("recalculateLayout", index, max_length, spacing);

        let layout = new BomProfileLayout(max_length, spacing);

        let bomItems = this.getProfiles(index);
        bomItems.forEach((bomItem) => {
            for (var _i = 0; _i < bomItem.instances; _i++) {
                layout.addChunk(bomItem.profile_length);
            }
        });

        this.profileLayouts[index] = layout;
        layout.calculate();

        console.log(layout);
        this.$forceUpdate();
    }

    addToLayout(): void {
        console.log(this.selectedItems);

        var selectedLayout: BomProfileLayout;
        if (this.profileLayouts.length == 0) {
            selectedLayout = new BomProfileLayout(3000, 2);
            this.profileLayouts.push(selectedLayout);
        } else {
            selectedLayout = this.profileLayouts[0];
        }

        this.selectedItems.forEach((selectedItem) => {
            selectedItem.layout_index = 0;
        });

        this.selectedItems = [];
    }

    constructor() {
        super();

        if (
            typeof generatedBOMTable === "undefined" &&
            typeof generatedBeamTable === "undefined"
        ) {
            var item = new BomItemFromFusion();
            item.name = "60x40";
            item.id = "0c1add5f-0229-4df7-9161-bb62a0d07fce";
            item.profile_size = "60x40";
            item.image = "Icon.png";
            item.instances = 2;
            item.boundingX = 1;
            item.boundingY = 1;
            item.boundingZ = 1;
            item.profile_length = 150;
            this.bomItems.push(item);

            item = new BomItemFromFusion();
            item.name = "60x40";
            item.id = "1c1add5f-0229-4df7-9161-bb62a0d07fce";
            item.profile_size = "60x40";
            item.image = "Icon.png";
            item.instances = 1;
            item.boundingX = 1;
            item.boundingY = 1;
            item.boundingZ = 1;
            item.is_profile = true;
            item.profile_length = 200;
            this.bomItems.push(item);

            item = new BomItemFromFusion();
            item.name = "80x40";
            item.id = "2c1add5f-0229-4df7-9161-bb62a0d07fce";
            item.profile_size = "80x40";
            item.image = "Icon.png";
            item.instances = 1;
            item.boundingX = 1;
            item.boundingY = 1;
            item.boundingZ = 1;
            item.is_profile = true;
            item.profile_length = 120;
            this.bomItems.push(item);
        } else {
            generatedBOMTable.forEach((generatedItem: BomItemFromFusion) => {
                generatedItem.layout_index = -1;
                this.bomItems.push(generatedItem);
            });

            generatedBeamTable.forEach((generatedItem: BomItemFromFusion) => {
                generatedItem.layout_index = -1;
                this.bomItems.push(generatedItem);
            });
        }
    }
}
</script>
