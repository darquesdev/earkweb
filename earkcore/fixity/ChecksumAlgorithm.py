class ChecksumAlgorithm:
    MD5, SHA256, NONE = range(3)

    @staticmethod
    def get(alg):
        """
        Constructor takes

        @type       alg: string
        @param      alg: Algorithm string
        @rtype:     ChecksumAlgorithm
        @return:    Checksum algorithm
        """
        if alg.lower() == "md5":
            return ChecksumAlgorithm.MD5
        elif alg.lower() == "sha256" or alg.lower() == "sha-256":
            return ChecksumAlgorithm.SHA256
        else:
            return ChecksumAlgorithm.NONE