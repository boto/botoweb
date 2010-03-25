<xsl:stylesheet version='1.0'
 xmlns:xsl='http://www.w3.org/1999/XSL/Transform'
 xmlns:bw='python://botoweb/xslt_functions'
 xmlns:boto='http://code.google.com/p/boto-web/wiki/FilterSchema'>
	<xsl:include href="base.xsl"/>
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
		<xsl:if test="bw:hasAuth('', ../../@name, @name)">
			<xsl:copy>
				<xsl:attribute name="perm"><xsl:if test="bw:hasAuth('GET', ../../@name, @name)">read</xsl:if> <xsl:if test="bw:hasAuth('PUT', ../../@name, @name)"> write</xsl:if></xsl:attribute>
				<xsl:apply-templates select="@*|node()"/>
			</xsl:copy>
		</xsl:if>
	</xsl:template>
	<xsl:template match="Index/api/properties/property[@name='created_by']|Index/api/properties/property[@name='modified_by']|Index/api/properties/property[@name='created_at']|Index/api/properties/property[@name='modified_at']|Index/api/properties/property[@name='sys_modstamp']" priority="10">
		<xsl:copy>
			<xsl:attribute name="perm">read</xsl:attribute>
			<xsl:apply-templates select="@*|node()"/>
		</xsl:copy>
	</xsl:template>

</xsl:stylesheet>
