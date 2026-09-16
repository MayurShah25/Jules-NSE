1. **Explain the AWS Elastic IP Process:**
   - The user needs to assign a static IP to their AWS instance because Zerodha requires it for live trading environments.
   - Provide a simple, step-by-step guide on how to allocate an Elastic IP in the AWS EC2 dashboard and associate it with their running instance.

2. **Warn about SSH changes:**
   - Remind the user that after assigning the Elastic IP, their previous dynamic IP will stop working. They must use the new Elastic IP for SSH (`scp`, `ssh`) and in their `deploy_to_aws.ps1` script from now on.
