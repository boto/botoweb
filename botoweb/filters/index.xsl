<xsl:stylesheet version='1.0'
 xmlns:xsl='http://www.w3.org/1999/XSL/Transform'
 xmlns:bw='python://botoweb/xslt_functions'
 xmlns:boto='http://code.google.com/p/boto-web/wiki/FilterSchema'>
	<xsl:include href="base.xsl"/>

	<!-- By default we pull all the authentications out of the DB -->
	<xsl:template match="Index/api">
		<xsl:if test="bw:hasAuth('GET', @name)">
			<xsl:copy>
				<xsl:apply-templates select="@*|node()"/>
			</xsl:copy>
		</xsl:if>
	</xsl:template>
	<xsl:template match ="Index/api/methods/*">
		<xsl:if test="bw:hasAuth(local-name(), ../../@name)">
			<xsl:copy>
				<xsl:apply-templates select="@*|node()"/>
			</xsl:copy>
		</xsl:if>
	</xsl:template>
	<xsl:template match ="Index/api/properties/property">
		<xsl:choose>
			<xsl:when test="bw:hasAuth('', ../../@name, @name)">
				<xsl:copy>
					<xsl:attribute name="perm"><xsl:if test="bw:hasAuth('GET', ../../@name, @name)">read</xsl:if> <xsl:if test="bw:hasAuth('PUT', ../../@name, @name)"> write</xsl:if></xsl:attribute>
					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:when>

			<!-- Some fields just simply must be readable -->
			<xsl:when test="@name='sys_modstamp'">
				<xsl:copy>
					<xsl:attribute name="perm">read</xsl:attribute>
					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:when>
			<xsl:when test="@name='name'">
				<xsl:copy>
					<xsl:attribute name="perm">read</xsl:attribute>
					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:when>
			<xsl:when test="@name='index'">
				<xsl:copy>
					<xsl:attribute name="perm">read</xsl:attribute>
					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:when>
			<xsl:when test="@name='deleted'">
				<xsl:copy>
					<xsl:attribute name="perm">read</xsl:attribute>
					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:when>

		</xsl:choose>
	</xsl:template>

	<!-- Mark all of these "auto" properties as read-only -->
	<xsl:template match="Index/api/properties/property[@name='created_by']|Index/api/properties/property[@name='modified_by']|Index/api/properties/property[@name='created_at']|Index/api/properties/property[@name='modified_at']|Index/api/properties/property[@name='sys_modstamp']" priority="5">
		<xsl:copy>
			<xsl:attribute name="perm">read</xsl:attribute>
			<xsl:apply-templates select="@*|node()"/>
		</xsl:copy>
	</xsl:template>

	<!-- Any properties of type query or calculated are read-only -->
	<xsl:template match="Index/api/properties/property[@type='query']|Index/api/properties/property[@calculated='true']" priority="5">
		<xsl:copy>
			<xsl:attribute name="perm">read</xsl:attribute>
			<xsl:apply-templates select="@*|node()"/>
		</xsl:copy>
	</xsl:template>

</xsl:stylesheet>
