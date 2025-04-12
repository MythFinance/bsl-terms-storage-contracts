import * as algokit from '@algorandfoundation/algokit-utils'
import { AlgorandClient } from '@algorandfoundation/algokit-utils'
import { LicensesFactory } from '../artifacts/licenses/LicensesClient'

// Below is a showcase of various deployment options you can use in TypeScript Client
export async function deploy() {
  algokit.Config.configure({
    debug: true,
    populateAppCallResources: true,
    // traceAll: true,
  })

  console.log('=== Deploying Licenses ===')

  const algorand = AlgorandClient.fromEnvironment()
  const deployer = await algorand.account.fromEnvironment('DEPLOYER')

  const factory = algorand.client.getTypedAppFactory(LicensesFactory, {
    defaultSender: deployer.addr,
  })

  const { appClient, result } = await factory.deploy({
    existingDeployments: { creator: deployer.addr, apps: {} }, // TO force redeploy
    onUpdate: 'append',
    onSchemaBreak: 'append',
  })

  // If app was just created fund the app account
  if (['create', 'replace'].includes(result.operationPerformed)) {
    await algorand.send.payment({
      amount: (0.2028).algo(),
      sender: deployer.addr,
      receiver: appClient.appAddress,
    })
  }

  await appClient.send.addProduct({
    args: {
      name: 'dualSTAKE Core',
      changeDate: 1830297600,
    },
  })

  const boxes = ['No additional uses are granted at this time.']

  await appClient.send.modifyUseGrants({
    args: {
      name: 'dualSTAKE Core',
      offset: 0,
      payload: boxes[0],
      finalChunk: true,
    },
  })

  await appClient.send.addProduct({
    args: {
      name: 'dualSTAKE Farms',
      changeDate: 1830297600,
    },
  })

  await appClient.send.modifyUseGrants({
    args: {
      name: 'dualSTAKE Farms',
      offset: 0,
      payload: boxes[0],
      finalChunk: true,
    },
  })
}
