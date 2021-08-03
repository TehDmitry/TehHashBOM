export default class BomItemFromFusion {
    id!: string;
    name!: string;
    image!: string;

    instances!: number;
    volume!: number;
    boundingX!: number;
    boundingY!: number;
    boundingZ!: number;
    is_profile!: boolean;
    profile_axis!: number;
    profile_length!: number;
    profile_size!: string;

    layout_index = -1;
}
