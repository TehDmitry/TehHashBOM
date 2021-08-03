import Material1D from "./Material1D";

export default class BomProfileLayout {
    readonly max_length: number;
    readonly spacing: number;

    chunks: Array<number> = [];
    unfitedChunks: Array<number> = [];
    rawBars: Array<Material1D> = [];

    constructor(max_length: number, spacing: number) {
        this.max_length = max_length;
        this.spacing = spacing;
    }

    getRawBars(): Array<Material1D> {
        return this.rawBars;
    }

    getUnfitedChunks(): Array<number> {
        return this.unfitedChunks;
    }

    addChunk(chunkLength: number): void {
        if (chunkLength > this.max_length) {
            this.unfitedChunks.push(chunkLength);
        } else {
            this.chunks.push(chunkLength);
        }
    }

    calculate(): void {
        const sortedChunks = this.chunks.sort((one: number, two: number) =>
            one > two ? -1 : 1
        );

        sortedChunks.forEach((chunk) => {
            // https://github.com/filipwodnicki/custo

            let chunkAdded = false;

            this.rawBars.forEach((bar) => {
                if (!chunkAdded && bar.lengthRemaining() >= chunk) {
                    bar.addChunk(chunk);
                    if (bar.lengthRemaining() > 0) {
                        bar.addChunk(this.spacing);
                    }

                    chunkAdded = true;
                }
            });

            if (!chunkAdded) {
                const bar = new Material1D(this.max_length);
                bar.addChunk(chunk);
                if (bar.lengthRemaining() > 0) {
                    bar.addChunk(this.spacing);
                }

                this.rawBars.push(bar);
            }
        });

        console.log(this.rawBars);
    }
}
