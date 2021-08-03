export default class Material1D {
    readonly length: number;

    chunks: Array<number> = [];

    constructor(max_length: number) {
        this.length = max_length;
    }

    addChunk(chunkLength: number): boolean {
        chunkLength = Number(chunkLength);
        if (chunkLength > this.lengthRemaining()) {
            return false;
        }

        this.chunks.push(chunkLength);

        return false;
    }

    lengthRemaining(): number {
        return this.length - this.lengthUsed();
    }

    lengthUsed(): number {
        return this.chunks.reduce((a, b) => a + b, 0);
    }
}
