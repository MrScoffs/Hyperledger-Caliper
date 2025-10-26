'use strict';

const { WorkloadModuleBase } = require('@hyperledger/caliper-core');
const crypto = require('crypto');

class ReportStatusWorkload extends WorkloadModuleBase {
    constructor() {
        super();
    }

    async submitTransaction() {
        // severity: 0=OK, 1=Warning, 2=Critical
        const severity = Math.floor(Math.random() * 3); // 0-2
        const statusHash = '0x' + crypto.randomBytes(32).toString('hex');
        const optionalDetails = `Worker ${this.workerIndex} status report - severity ${severity}`;

        const args = {
            contract: 'NodeHealthMonitor',
            verb: 'reportStatus',
            args: [severity.toString(), statusHash, optionalDetails],
        };

        await this.sutAdapter.sendRequests(args);
    }
}

function createWorkloadModule() {
    return new ReportStatusWorkload();
}

module.exports.createWorkloadModule = createWorkloadModule;
