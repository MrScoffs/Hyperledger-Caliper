'use strict';

const { WorkloadModuleBase } = require('@hyperledger/caliper-core');

class GetLatestStatusWorkload extends WorkloadModuleBase {
    constructor() {
        super();
    }

    async submitTransaction() {
        const nodeAddress = '0x0000000000000000000000000000000000000001';
        const args = {
            contract: 'NodeHealthMonitor',
            verb: 'getLatestStatus',
            args: [nodeAddress],
        };
        await this.sutAdapter.sendRequests(args);
    }
}

function createWorkloadModule() {
    return new GetLatestStatusWorkload();
}

module.exports.createWorkloadModule = createWorkloadModule;
