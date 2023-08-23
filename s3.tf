resource "aws_s3_bucket" "vision_speak" {
  bucket = "vision-speack-${var.environment}"
}

resource "aws_s3_bucket_public_access_block" "vision_speak" {
  bucket                  = aws_s3_bucket.vision_speak.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "vision_speak" {
  bucket = aws_s3_bucket.vision_speak.id
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}
