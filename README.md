# Ansible AWS ElasticSearch snapshots module
Just include this module in your 'library' folder and you could create a snapshot repository on S3 for your AWS ElasticSearch snapshots. Use it in a playbook like:

---

- hosts: localhost
  tasks:
    - name: "Registering Snapshopt Repository in ElasticSearch"
      register_snapshot_repository:
        profile: "preproduction"
        region: "eu-west-1"
        es_host: "some_aws_elasticsearch_host"
        role_arn: "arn:aws:iam::891310123456:role/SomeRole"
        bucket: "elasticsearch_snapshots"
        repository_name: "s3snapshots"