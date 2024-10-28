data "aws_iam_policy_document" "policy_pset_c_security" {
  source_policy_documents = [file("${path.module}/policy_pset_c_security.json")]
}


module "iam_policy" {
  source = "terraform-aws-modules/iam/aws//modules/iam-policy"

  name        = "policy_pset_c_security"
  path        = "/"
  description = "policy_pset_c_security"
  tags        = { ManagedBy = "Terraform" }

  policy = data.aws_iam_policy_document.policy_pset_c_security.json
}
